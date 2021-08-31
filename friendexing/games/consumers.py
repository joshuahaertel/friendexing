import json
import logging
import re
from time import time
from typing import Set

from channels.generic.http import AsyncHttpConsumer
from channels.generic.websocket import AsyncWebsocketConsumer

from games.constants import NUM_TOP_PLAYERS, MessageSeverityLevel
from games.family_search import FamilySearchJob
from games.models import Phases
from games.orm import GameRedisORM, PlayerRedisORM, BatchRedisORM, \
    ImageModelORM

LOGGER = logging.getLogger(__name__)

UUID_REGEX = re.compile(
    r'\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b',
)


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
        await self.send_images()
        await self.send_scores()
        await self.send_state()

    async def send_images(self, event=None):
        if event:
            batch_ids = [event['batch_id']]
        else:
            batch_ids = await GameRedisORM.get_batches(self.game_id) or []

        for batch_id in batch_ids:
            # todo: append all things to the list at once
            image_ids = await BatchRedisORM.get_image_ids(batch_id)
            await self.send(text_data=json.dumps({
                'type': 'add_images',
                'images': [
                    {
                        'image_url': f'/images/{image_id}',
                        'thumbnail_url': f'/images/{image_id}/thumbnail',
                    }
                    for image_id in image_ids
                ]
            }))

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
        await self.send_images()
        await self.send_scores()
        await self.send_guesses()
        await self.send_state()

    async def send_images(self, event=None):
        if event:
            batch_ids = [event['batch_id']]
        else:
            batch_ids = await GameRedisORM.get_batches(self.game_id) or []

        for batch_id in batch_ids:
            # todo: append all things to the list at once
            image_ids = await BatchRedisORM.get_image_ids(batch_id)
            await self.send(text_data=json.dumps({
                'type': 'add_images',
                'images': [
                    {
                        'image_url': f'/images/{image_id}',
                        'thumbnail_url': f'/images/{image_id}/thumbnail',
                    }
                    for image_id in image_ids
                ]
            }))

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
            if game_state.phase != Phases.WAIT:
                await GameRedisORM.update_phase(self.game_id, Phases.WAIT, 0)
                await self.channel_layer.group_send(
                    self.game_id,
                    {
                        'type': 'send_state',
                    }
                )

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
            # todo: after two hours player iterator expires. Refresh those
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
        elif message_type == 'add_batch':
            batch_url = text_data_json['batch_url']
            matches = UUID_REGEX.findall(batch_url)
            if not matches:
                return  # todo: inform Bad URL
            batch_id = matches[-1]
            # todo: lots of corner case errors here
            image_ids = await BatchRedisORM.get_image_ids(batch_id)
            if image_ids:
                await GameRedisORM.add_existing_batch(batch_id, self.game_id)
            else:
                batch_job = FamilySearchJob(batch_id)
                batch = await batch_job.run()
                await GameRedisORM.add_new_batch(self.game_id, batch)
            await self.channel_layer.group_send(
                self.game_id,
                {
                    'type': 'send_images',
                    'batch_id': batch_id,
                }
            )
        else:
            LOGGER.debug('Unrecognized message: %s', text_data_json)

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


with open('games/static/games/demo-1.jpg', mode='rb') as image:
    IMAGE_BYTES = image.read()


class ImageConsumer(AsyncHttpConsumer):
    async def handle(self, body):
        # TODO: check image permissions
        image_id = self.scope['url_route']['kwargs']['image_id']
        image_bytes = await ImageModelORM.get_image_bytes(image_id)
        await self.send_response(200, image_bytes or IMAGE_BYTES)


class ThumbnailConsumer(AsyncHttpConsumer):
    async def handle(self, body):
        image_id = self.scope['url_route']['kwargs']['image_id']
        image_bytes = await ImageModelORM.get_thumbnail_bytes(image_id)
        await self.send_response(200, image_bytes or IMAGE_BYTES)
