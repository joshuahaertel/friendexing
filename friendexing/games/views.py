from typing import Optional

from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.views.generic import FormView

from games.forms import GameForm, PlayerForm
from games.models import Game

GAME_EXPIRES_TIME = 120


class GameCreate(FormView):
    template_name = 'games/create.html'
    form_class = GameForm
    game: Optional[Game] = None

    def form_valid(self, form: GameForm):
        self.game = form.create_game()
        response = super().form_valid(form)
        response.set_cookie(
            key=str(self.game.id),
            value=str(self.game.players[0].id),
            expires=120,
        )
        return response

    def get_success_url(self):
        return f'/games/{self.game.id}/'


@csrf_protect
def game_view(request: HttpRequest, game_id):
    game_id_str = str(game_id)
    player_id = request.COOKIES.get(game_id_str)
    if player_id:
        response = render(request, 'games/play.html')
        response.set_cookie(
            key=game_id_str,
            value=player_id,
            expires=GAME_EXPIRES_TIME,
        )
        return response
    else:
        return redirect(f'/games/{game_id}/join/')


class PlayerCreate(FormView):
    template_name = 'games/join.html'
    form_class = PlayerForm

    def form_valid(self, form: PlayerForm):
        player = form.create_player()
        response = super().form_valid(form)
        response.set_cookie(
            key=str(self.kwargs['game_id']),
            value=str(player.id),
            expires=GAME_EXPIRES_TIME,
        )
        return response

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['game_id'] = self.kwargs['game_id']
        return context_data

    def get_success_url(self):
        return f'/games/{self.kwargs["game_id"]}/'
