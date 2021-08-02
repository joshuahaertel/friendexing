import json
from time import time
from typing import Set

from channels.generic.websocket import AsyncWebsocketConsumer

from games.constants import NUM_TOP_PLAYERS
from games.orm import GameRedisORM, PlayerRedisORM


class PlayConsumer(AsyncWebsocketConsumer):
    game_id: str
    game_group_id: str
    admin_group_id: str
    player_id: str

    async def connect(self):
        self.game_id = str(self.scope['url_route']['kwargs']['game_id'])
        self.game_group_id = self.game_id
        self.player_id = str(self.scope['url_route']['kwargs']['player_id'])
        self.admin_group_id = f'admin_{self.game_group_id}'

        await self.channel_layer.group_add(
            self.game_group_id,
            self.channel_name,
        )
        await self.accept()
        await self.send_scores()

    async def send_scores(self):
        top_players = await GameRedisORM.get_top_player_scores(self.game_id)
        for top_player in top_players:
            if top_player.player_id == self.player_id:
                break
        else:
            player_score = await PlayerRedisORM.get_player_score(
                self.player_id,
            )
            top_players.append(player_score)
        await self.send(text_data=json.dumps({
            'type': 'scores',
            'num_top_players': NUM_TOP_PLAYERS,
            'scores': [
                top_player.serialize_as_json()
                for top_player in top_players
            ],
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.game_group_id,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        received_time = time()
        text_data_json = json.loads(text_data)
        guess_end_time = await GameRedisORM.get_guess_end_time(self.game_id)
        if not guess_end_time:
            await self.reject_answer()
            return
        score = guess_end_time - received_time
        if score <= 0:
            await self.reject_answer()
            return

        # todo: save guess and score to user
        raw_guess: str = text_data_json['guess']
        # todo: cleaning?
        cleaned_guess = raw_guess.strip().lower()
        await GameRedisORM.add_guess(self.game_id, cleaned_guess)

        await self.channel_layer.group_send(
            self.admin_group_id,
            {
                'type': 'new_guess',
            }
        )

    async def reject_answer(self):
        await self.send(text_data=json.dumps({
            'type': 'guess',
            'message': 'We are no longer accepting answers for this field',
        }))

    async def correct_answer(self, event):
        await self.send(text_data=json.dumps({
            'answer': event['answer'],
        }))
        await self.send_scores()


class AdminConsumer(AsyncWebsocketConsumer):
    game_id: str
    admin_id: str

    async def connect(self):
        self.game_id = str(self.scope['url_route']['kwargs']['game_id'])
        self.admin_id = f'admin_{self.game_id}'

        await self.channel_layer.group_add(
            self.game_id,
            self.channel_name
        )
        await self.channel_layer.group_add(
            self.admin_id,
            self.channel_name
        )

        await self.accept()
        await self.send_scores()

    async def send_scores(self):
        all_scores = await GameRedisORM.get_player_scores(self.game_id)
        await self.send(text_data=json.dumps({
            'type': 'scores',
            'scores': [
                player_score.serialize_as_json()
                for player_score in all_scores
            ],
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.game_id,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            self.admin_id,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        display_answer = text_data_json['display_answer']
        correct_answers: Set[str] = set(text_data_json['correct_answers'])
        player_scores = []
        async for player in GameRedisORM.player_iterator(self.game_id):
            if player.guess in correct_answers:
                player.score += player.potential_points
            player.guess = ''
            player.guess_id = ''
            player.potential_points = 0
            player_scores.append(player.score)
            player_scores.append(player.id)
            await PlayerRedisORM(player).save()
        await GameRedisORM.set_player_scores(self.game_id, player_scores)

        await self.channel_layer.group_send(
            self.game_id,
            {
                'type': 'correct_answer',
                'answer': display_answer,
            }
        )

    async def new_guess(self, _):
        # todo: validate in guessing state
        await self.send(text_data=json.dumps({
            'type': 'new_guess',
            'guesses': await GameRedisORM.get_guesses(self.game_id)
        }))

    async def correct_answer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'correct_answer',
            'answer': event['answer'],
        }))
        await self.send_scores()
