import json
from time import time
from typing import Set

from channels.generic.websocket import AsyncWebsocketConsumer

from games.constants import NUM_TOP_PLAYERS, MessageSeverityLevel
from games.models import Phases
from games.orm import GameRedisORM, PlayerRedisORM


# todo: show previous answer upon connection
# todo: state management
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
        await self.send_state()

    async def send_scores(self, _=None):
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
            'type': 'update_scores',
            'num_top_players': NUM_TOP_PLAYERS,
            'scores': [
                top_player.serialize_as_json()
                for top_player in top_players
            ],
        }))

    async def send_state(self, *_):
        game_state = await GameRedisORM.get_game_state(self.game_id)
        time_remaining = int(game_state.guess_end_time - time())
        if time_remaining < 0:
            phase = Phases.WAIT
        else:
            phase = Phases.PLAY
        await self.send(text_data=json.dumps({
            'type': 'update_state',
            'phase': phase,
            'time_remaining': time_remaining,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.game_group_id,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        received_time = time()
        text_data_json = json.loads(text_data)
        game_state = await GameRedisORM.get_game_state(self.game_id)
        if not game_state:
            await self.send_message(
                message=('Game no longer exists, please refresh and create '
                         'a new one'),
                severity=MessageSeverityLevel.DANGER,
            )
            return
        if game_state.phase != Phases.PLAY:
            await self.send_message(
                message='Not accepting answers',
                severity=MessageSeverityLevel.WARNING
            )
            return
        potential_score_delta = int(
            game_state.guess_end_time - received_time
        ) + 1
        if potential_score_delta <= 0:
            await self.send_message(
                message='Missed deadline to submit an answer',
                severity=MessageSeverityLevel.WARNING
            )
            return

        raw_guess: str = text_data_json['guess']
        cleaned_guess = raw_guess.strip().lower()
        player = await PlayerRedisORM.get_player(self.player_id)
        old_guess = player.guess
        if old_guess == cleaned_guess:
            await self.send_message(
                message=('Duplicate/similar-enough response submitted. '
                         'Using first submission to increase points '
                         '(this will not affect if answer is considered '
                         'correct)'
                         ),
                severity=MessageSeverityLevel.INFO,
            )
            return
        await PlayerRedisORM.save_guess(
            self.player_id,
            cleaned_guess,
            potential_score_delta,
        )
        await GameRedisORM.add_guess(self.game_id, cleaned_guess)
        if old_guess:
            await GameRedisORM.remove_guess(self.game_id, old_guess)

        await self.channel_layer.group_send(
            self.admin_group_id,
            {
                'type': 'new_guess',
            }
        )
        await self.send_message(
            message=(f'Guess submitted successfully! '
                     f'Transformed to: "{cleaned_guess}" '
                     f'Potential points: {potential_score_delta}'
                     ),
            severity=MessageSeverityLevel.INFO,
        )

    async def send_message(self, message, severity):
        await self.send(text_data=json.dumps({
            'type': 'show_message',
            'message': message,
            'severity': severity,
        }))

    async def correct_answer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'show_answer',
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
        await self.send_guesses()
        await self.send_state()

    async def send_scores(self, _=None):
        all_scores = await GameRedisORM.get_player_scores(self.game_id)
        await self.send(text_data=json.dumps({
            'type': 'update_scores',
            'scores': [
                player_score.serialize_as_json()
                for player_score in all_scores
            ],
        }))

    async def send_state(self, *_):
        game_state = await GameRedisORM.get_game_state(self.game_id)
        time_remaining = int(game_state.guess_end_time - time())
        if time_remaining < 0:
            phase = Phases.WAIT
        else:
            phase = Phases.PLAY
        await self.send(text_data=json.dumps({
            'type': 'update_state',
            'phase': phase,
            'time_remaining': time_remaining,
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
        # todo: state checking
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']
        game_state = await GameRedisORM.get_game_state(self.game_id)
        if message_type == 'submit_answer':
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
            # todo: fix corner case where admin sends an answer and no one
            # has submitted anything
            await GameRedisORM.set_player_scores(self.game_id, player_scores)
            await GameRedisORM.clear_guesses(self.game_id)

            await self.channel_layer.group_send(
                self.game_id,
                {
                    'type': 'correct_answer',
                    'answer': display_answer,
                }
            )
        elif message_type == 'update_phase':
            # todo: checks of current phase
            guess_end_time = time() + game_state.total_time_to_guess
            await GameRedisORM.update_phase(
                self.game_id,
                Phases.PLAY,
                guess_end_time,
            )
            await self.channel_layer.group_send(
                self.game_id,
                {
                    'type': 'send_state',
                }
            )

    async def new_guess(self, _):
        await self.send_guesses()

    async def send_guesses(self):
        # todo: validate in guessing state
        await self.send(text_data=json.dumps({
            'type': 'update_guesses',
            'guesses': await GameRedisORM.get_guesses(self.game_id)
        }))

    async def correct_answer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'show_answer',
            'answer': event['answer'],
        }))
        await self.send_scores()
