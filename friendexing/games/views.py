from typing import Optional, Any, Dict
from uuid import UUID

from django.http import HttpRequest, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.views.generic import FormView

from games.forms import GameForm, PlayerForm
from games.models import Game

GAME_EXPIRES_TIME = 120


class GameCreate(FormView):
    template_name = 'games/create.html'  # noqa: F841
    form_class = GameForm  # noqa: F841
    game: Optional[Game] = None

    def form_valid(self, form: GameForm) -> HttpResponseRedirect:
        self.game = form.create_game()
        response = super().form_valid(form)
        response.set_cookie(
            key=str(self.game.id),
            value=str(self.game.players[0].id),
            expires=120,
        )
        return response

    def get_success_url(self) -> str:
        return f'/games/{self.game.id}/'


@csrf_protect
def game_view(request: HttpRequest, game_id: UUID) -> HttpResponse:
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
    template_name = 'games/join.html'  # noqa: F841
    form_class = PlayerForm  # noqa: F841

    def form_valid(self, form: PlayerForm) -> HttpResponseRedirect:
        player = form.create_player()
        response = super().form_valid(form)
        response.set_cookie(
            key=str(self.kwargs['game_id']),
            value=str(player.id),
            expires=GAME_EXPIRES_TIME,
        )
        return response

    def get_context_data(self, **kwargs: Dict['str', Any]) -> Dict[str, Any]:
        context_data: Dict[str, Any] = super().get_context_data(**kwargs)
        context_data['game_id'] = self.kwargs['game_id']
        return context_data

    def get_success_url(self) -> str:
        return f'/games/{self.kwargs["game_id"]}/'
