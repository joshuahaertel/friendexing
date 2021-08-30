import asyncio
from asyncio import AbstractEventLoop
from typing import Optional, Dict

import aioredis
from aioredis import Redis
from django.conf import settings

from games.constants import GAME_EXPIRY_SECONDS, TOP_PLAYER_INDEX
from games.helper_models import PlayerScore
from games.models import Game, Player, State, Batch, ImageModel


class RedisORM:
    _redis_pools: Dict[AbstractEventLoop, Redis] = {}

    def __init__(self, obj):
        self.obj = obj

    async def save(
            self,
            redis_pool: Redis = None,
    ):
        raise NotImplementedError

    @staticmethod
    async def get_redis_pool(redis_pool: Redis = None, maxsize=10):
        if redis_pool:
            return redis_pool
        loop = asyncio.get_event_loop()
        pool = RedisORM._redis_pools.get(loop)
        if pool is None:
            RedisORM._redis_pools[loop] = await aioredis.create_redis_pool(
                **settings.REDIS_CONFIGURATION,
                maxsize=maxsize,
                encoding='utf-8',
            )
        return RedisORM._redis_pools[loop]


class GameRedisORM(RedisORM):
    obj: Game

    async def save(
            self,
            redis_pool: Redis = None,
    ):
        game = self.obj
        game_id = game.id
        redis_pool = await self.get_redis_pool(redis_pool)
        await self.save_players(game, game_id, redis_pool)
        await self.save_state(game, game_id, redis_pool)

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

    @classmethod
    async def add_batch(cls, game_id, batch, redis_pool=None):
        batches_key = f'batches:{game_id}'
        redis_pool = await cls.get_redis_pool(redis_pool)
        await BatchRedisORM(batch).save()
        await redis_pool.rpush(batches_key, batch.id)
        await redis_pool.expire(batches_key, GAME_EXPIRY_SECONDS)

    @classmethod
    async def get_batches(cls, game_id):
        batches_key = f'batches:{game_id}'
        redis_pool = await cls.get_redis_pool()
        return await redis_pool.lrange(batches_key, 0, -1)

    @staticmethod
    async def save_state(game, game_id, redis_pool):
        state = game.state
        await GameRedisORM.set_state(game_id, state, redis_pool)

    @classmethod
    async def set_state(cls, game_id, state, redis_pool=None):
        redis_pool = await cls.get_redis_pool(redis_pool)
        game_state_key = f'state:{game_id}'
        if state.should_randomize_fields:
            should_randomize_fields = 1
        else:
            should_randomize_fields = 0
        await redis_pool.hmset_dict(game_state_key, {
            'total_time_to_guess': state.total_time_to_guess,
            'should_randomize_fields': should_randomize_fields,
            'phase': state.phase,
            'admin_id': str(state.admin_id),
            'guess_end_time': 0,
        })
        await redis_pool.expire(game_state_key, GAME_EXPIRY_SECONDS)

    @classmethod
    async def get_game_state(cls, game_id, redis_pool=None) -> Optional[State]:
        redis_pool = await cls.get_redis_pool(redis_pool)
        values = await redis_pool.hmget(
            f'state:{game_id}',
            'total_time_to_guess',
            'should_randomize_fields',
            'phase',
            'admin_id',
            'guess_end_time',
        )
        phase = values[2]
        if phase is None:
            return None
        return State(
            total_time_to_guess=int(values[0]),
            # note: Going off of truth-y here
            should_randomize_fields=values[1],
            phase=phase,
            admin_id=values[3],
            guess_end_time=float(values[4] or 0),
        )

    @classmethod
    async def add_player(cls, game_id, player, redis_pool):
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
    async def add_guess(cls, game_id, guess):
        redis_pool = await cls.get_redis_pool()
        guesses_key = f'guesses:{game_id}'
        await redis_pool.zincrby(guesses_key, 1, guess)

    @classmethod
    async def remove_guess(cls, game_id, old_guess):
        redis_pool = await cls.get_redis_pool()
        guesses_key = f'guesses:{game_id}'
        await redis_pool.zincrby(guesses_key, -1, old_guess)

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
        return scores_list

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

    @classmethod
    async def update_phase(cls, game_id, phase, guess_end_time):
        redis_pool = await cls.get_redis_pool()
        game_state_key = f'state:{game_id}'
        pairs = [
            'phase', phase,
            'guess_end_time', guess_end_time,
        ]
        await redis_pool.hmset(
            game_state_key,
            *pairs,
        )
        await redis_pool.expire(game_state_key, GAME_EXPIRY_SECONDS)

    @classmethod
    async def clear_guesses(cls, game_id):
        redis_pool = await cls.get_redis_pool()
        guesses_key = f'guesses:{game_id}'
        await redis_pool.delete(guesses_key)

    @classmethod
    async def verify_game_exists(cls, game_id, redis_pool):
        game_state_key = f'state:{game_id}'
        phase = await redis_pool.hget(game_state_key, 'phase')
        return bool(phase)


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
    async def get_player(cls, player_id, redis_pool=None):
        redis_pool = await cls.get_redis_pool(redis_pool)
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
            score=int(results[1]),
            guess_id=results[2],
            guess=results[3],
            potential_points=int(results[4]),
        )

    @classmethod
    async def save_guess(cls, player_id, guess, potential_score_delta):
        redis_pool = await cls.get_redis_pool()
        player_key = f'player:{player_id}'
        player_dict = {
            'guess': guess,
            'potential_points': potential_score_delta,
        }
        await redis_pool.hmset_dict(player_key, player_dict)
        await redis_pool.expire(player_key, GAME_EXPIRY_SECONDS)


class BatchRedisORM(RedisORM):
    obj: Batch

    async def save(
            self,
            redis_pool: Redis = None,
    ):
        batch = self.obj
        redis_pool = await self.get_redis_pool(redis_pool)
        batch_key = f'batch:{batch.id}'
        image_ids = []
        for image in batch.image_models:
            await ImageModelORM(image).save(redis_pool)
            image_ids.append(image.id)
        await redis_pool.rpush(batch_key, *image_ids)
        await redis_pool.expire(batch_key, GAME_EXPIRY_SECONDS)

    @classmethod
    async def get_image_ids(cls, batch_id):
        redis_pool = await cls.get_redis_pool()
        batch_key = f'batch:{batch_id}'
        return await redis_pool.lrange(batch_key, 0, -1)


class ImageModelORM(RedisORM):
    obj: ImageModel

    async def save(
            self,
            redis_pool: Redis = None,
    ) -> None:
        image = self.obj
        redis_pool = await self.get_redis_pool(redis_pool)
        image_key = f'image:{image.id}'
        image_dict = {
            'image_bytes': image.image_bytes,
            'thumbnail_bytes': image.thumbnail_bytes,
        }
        await redis_pool.hmset_dict(image_key, image_dict)
        await redis_pool.expire(image_key, GAME_EXPIRY_SECONDS)

    @classmethod
    async def get_image_bytes(cls, image_id):
        image_key = f'image:{image_id}'
        redis_pool = await cls.get_redis_pool()
        return await redis_pool.hget(
            image_key,
            'image_bytes',
            encoding=None,
        )

    @classmethod
    async def get_thumbnail_bytes(cls, image_id):
        image_key = f'image:{image_id}'
        redis_pool = await cls.get_redis_pool()
        return await redis_pool.hget(
            image_key,
            'thumbnail_bytes',
            encoding=None,
        )
