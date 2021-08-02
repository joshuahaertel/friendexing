import json

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
            'answer': None,
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
        text_data_json = json.loads(text_data)
        guess = text_data_json['guess']
        # Calculate elapsed time
        elapsed_time = text_data_json['elapsed_time']
        # save guess
        # publish new guess for admin

        await self.channel_layer.group_send(
            self.admin_group_id,
            {
                'type': 'new_guess',
                'guess': guess,
                'elapsed_time': elapsed_time,
            }
        )

    async def correct_answer(self, event):
        answer = event['answer']
        scores = event['scores']

        await self.send(text_data=json.dumps({
            'answer': answer,
            'scores': scores,
        }))


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
            'answer': None,
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
        # Go through each player
        # calculate score
        # publish new scores

        await self.channel_layer.group_send(
            self.game_id,
            {
                'type': 'correct_answer',
                'answer': text_data_json['correct_answer'],
                'scores': [
                    {'name': 'steve', 'score': 34},
                    {'name': 'Ryan', 'score': 4321},
                ],
            }
        )

    async def new_guess(self, event):
        # Get all guesses, send aggregate
        guess = event['guess']
        elapsed_time = event['elapsed_time']

        await self.send(text_data=json.dumps({
            'type': 'new_guess',
            'name': 'gus',
            'guess': guess,
            'elapsed_time': elapsed_time,
        }))

    async def correct_answer(self, event):
        answer = event['answer']
        scores = event['scores']

        await self.send(text_data=json.dumps({
            'type': 'correct_answer',
            'answer': answer,
            'scores': scores,
        }))
