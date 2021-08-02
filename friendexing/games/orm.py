from typing import Optional

import aioredis
from aioredis import Redis
from django.conf import settings

from games.constants import GAME_EXPIRY_SECONDS, TOP_PLAYER_INDEX
from games.helper_models import PlayerScore
from games.models import Game, Player, State


class RedisORM:
    _redis_pool: Redis = None

    def __init__(self, obj):
        self.obj = obj

    async def save(
            self,
            redis_pool: Redis = None,
    ):
        raise NotImplementedError

    @staticmethod
    async def get_redis_pool(redis_pool: Redis = None):
        if redis_pool:
            return redis_pool
        if RedisORM._redis_pool is None:
            RedisORM._redis_pool = await aioredis.create_redis_pool(
                **settings.REDIS_CONFIGURATION,
                encoding='utf-8',
            )
        return RedisORM._redis_pool


class GameRedisORM(RedisORM):
    obj: Game

    async def save(
            self,
            redis_pool: Redis = None,
    ):
        game = self.obj
        game_id = game.id
        redis_pool = await self.get_redis_pool(redis_pool)
        await self.save_settings(game, game_id, redis_pool)
        await self.save_players(game, game_id, redis_pool)
        # await self.save_batches(game, game_id, redis_pool)
        await self.save_state(game, game_id, redis_pool)

    @staticmethod
    async def save_settings(game, game_id, redis_pool):
        game_settings = game.settings
        settings_key = f'settings:{game_id}'
        if game_settings.should_randomize_fields:
            should_randomize_fields = 1
        else:
            should_randomize_fields = 0
        settings_dict = {
            'total_time_to_guess': game_settings.total_time_to_guess,
            'should_randomize_fields': should_randomize_fields,
        }
        await redis_pool.hmset_dict(settings_key, settings_dict)
        await redis_pool.expire(settings_key, GAME_EXPIRY_SECONDS)

    @staticmethod
    async def save_players(game, game_id, redis_pool):
        players_key = f'players:{game_id}'
        player_ids = []
        for player in game.players:
            player_ids.append(player.score)
            player_ids.append(str(player.id))
            await PlayerRedisORM(player).save()
        await redis_pool.zadd(players_key, *player_ids)
        await redis_pool.expire(players_key, GAME_EXPIRY_SECONDS)

    @staticmethod
    async def save_batches(game, game_id, redis_pool):
        batch_key = f'batches:{game_id}'
        batch_ids = []
        for batch in game.batches:
            await BatchRedisORM(batch).save()
            batch_ids.append(batch.id)
        await redis_pool.rpush(batch_key, *batch_ids)
        await redis_pool.expire(batch_key, GAME_EXPIRY_SECONDS)

    @staticmethod
    async def save_state(game, game_id, redis_pool):
        state = game.state
        game_state_key = f'state:{game_id}'
        await redis_pool.hmset_dict(game_state_key, {
            'phase': state.phase,
            'admin_id': str(state.admin_id),
        })
        await redis_pool.expire(game_state_key, GAME_EXPIRY_SECONDS)

    @classmethod
    async def get_game_state(cls, game_id) -> Optional[State]:
        print('getting game state')
        redis_pool = await cls.get_redis_pool()
        print('got redis pool', redis_pool)
        values = await redis_pool.hmget(
            f'state:{game_id}',
            'phase',
            'admin_id',
        )
        print('got values', values)
        phase = values[0]
        if phase is None:
            return None
        return State(
            phase=phase,
            admin_id=values[1],
        )

    @classmethod
    async def add_player(cls, game_id, player):
        redis_pool = await cls.get_redis_pool()
        await PlayerRedisORM(player).save()
        players_key = f'players:{game_id}'
        await redis_pool.zadd(players_key, player.score, str(player.id))
        await redis_pool.expire(players_key, GAME_EXPIRY_SECONDS)

    @classmethod
    async def get_top_player_scores(cls, game_id):
        return await cls.get_player_scores(game_id, stop=TOP_PLAYER_INDEX)

    @classmethod
    async def get_player_scores(cls, game_id, stop=-1):
        redis_pool = await cls.get_redis_pool()
        players_key = f'players:{game_id}'
        top_player_ids = await redis_pool.zrevrange(
            players_key,
            start=0,
            stop=stop,
        )
        return [
            await PlayerRedisORM.get_player_score(player_id, redis_pool)
            for player_id in top_player_ids
        ]

    @classmethod
    async def get_guess_end_time(cls, game_id) -> float:
        redis_pool = await cls.get_redis_pool()
        state_key = f'state:{game_id}'
        return await redis_pool.hget(
            state_key,
            'guess_end_time',
        )

    @classmethod
    async def add_guess(cls, game_id, guess):
        redis_pool = await cls.get_redis_pool()
        guesses_key = f'guesses:{game_id}'
        await redis_pool.zincrby(guesses_key, 1, guess)

    @classmethod
    async def get_guesses(cls, game_id):
        redis_pool = await cls.get_redis_pool()
        guesses_key = f'guesses:{game_id}'
        scores_list = await redis_pool.zrevrange(
            guesses_key,
            start=0,
            stop=-1,
            withscores=True,
        )
        return [
            (scores_list[index], scores_list[index + 1])
            for index in range(0, len(scores_list), 2)
        ]

    @classmethod
    async def player_iterator(cls, game_id):
        redis_pool = await cls.get_redis_pool()
        players_key = f'players:{game_id}'
        player_ids = await redis_pool.zrange(players_key)
        for player_id in player_ids:
            player = await PlayerRedisORM.get_player(player_id, redis_pool)
            if player:
                yield player

    @classmethod
    async def set_player_scores(cls, game_id, player_scores):
        redis_pool = await cls.get_redis_pool()
        players_key = f'players:{game_id}'
        redis_pool.zadd(
            players_key,
            *player_scores,
        )


class PlayerRedisORM(RedisORM):
    obj: Player

    async def save(
            self,
            redis_pool: Redis = None,
    ):
        player = self.obj
        redis_pool = await self.get_redis_pool(redis_pool)
        player_key = f'player:{player.id}'
        player_dict = {
            'name': player.name,
            'score': player.score,
            'guess_id': player.guess_id,
            'guess': player.guess,
            'potential_points': player.potential_points,
        }
        await redis_pool.hmset_dict(player_key, player_dict)
        await redis_pool.expire(player_key, GAME_EXPIRY_SECONDS)

    @classmethod
    async def get_player_score(cls, player_id, redis_pool=None):
        player_key = f'player:{player_id}'
        redis_pool = await cls.get_redis_pool(redis_pool)
        results = await redis_pool.hmget(
            player_key,
            'name',
            'score',
        )
        return PlayerScore(
            name=results[0],
            score=results[1],
            player_id=player_id
        )

    @classmethod
    async def get_player(cls, player_id, redis_pool):
        player_key = f'player:{player_id}'
        results = await redis_pool.hmget(
            player_key,
            'name',
            'score',
            'guess_id',
            'guess',
            'potential_points',
        )
        name = results[0]
        if name is None:
            return None
        return Player(
            id_=player_id,
            name=name,
            score=results[1],
            guess_id=results[2],
            guess=results[3],
            potential_points=results[4],
        )


class BatchRedisORM(RedisORM):
    async def save(
            self,
            redis_pool: Redis = None,
    ):
        pass
