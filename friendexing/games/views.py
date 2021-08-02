from datetime import datetime
from typing import Optional, Any, Dict
from uuid import UUID

from django.forms import BaseForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_protect
from django.views.generic import FormView

from games.constants import GAME_EXPIRY_DELTA
from games.forms import GameForm, PlayerForm
from games.models import Game, State
from games.orm import GameRedisORM


def get_expiry() -> datetime:
    return now() + GAME_EXPIRY_DELTA


class GameCreate(FormView):
    template_name = 'games/create.html'  # noqa: F841
    form_class = GameForm  # noqa: F841
    game: Optional[Game] = None

    def form_valid(self, form: BaseForm) -> HttpResponse:
        assert isinstance(form, GameForm)
        self.game = game = form.create_game()
        response = super().form_valid(form)
        response.set_cookie(
            key=str(game.id),
            value=str(game.players[0].id),
            expires=get_expiry(),
        )
        GameRedisORM(game).save_sync()
        return response

    def get_success_url(self) -> str:
        assert self.game
        return f'/games/{self.game.id}/'


@csrf_protect
def game_view(request: HttpRequest, game_id: UUID) -> HttpResponse:
    game_id_str = str(game_id)
    player_id = request.COOKIES.get(game_id_str)
    if player_id:
        game_info: Optional[State] = GameRedisORM.get_game_state(game_id_str)
        if game_info is None:
            # todo: notify game expired
            return redirect(f'/games/create/')
        else:
            if player_id == game_info.admin_id:
                response = render(request, 'games/admin.html')
            else:
                # todo: check that player in list
                response = render(request, 'games/play.html')
        response.set_cookie(
            key=game_id_str,
            value=player_id,
            expires=get_expiry(),
        )
        return response
    else:
        return redirect(f'/games/{game_id}/join/')


class PlayerCreate(FormView):
    template_name = 'games/join.html'  # noqa: F841
    form_class = PlayerForm  # noqa: F841

    def form_valid(self, form: BaseForm) -> HttpResponse:
        assert isinstance(form, PlayerForm)
        player = form.create_player()
        response = super().form_valid(form)
        game_id = str(self.kwargs['game_id'])
        response.set_cookie(
            key=game_id,
            value=str(player.id),
            expires=get_expiry(),
        )
        GameRedisORM.add_player(game_id, player)
        return response

    def get_context_data(self, **kwargs: Dict['str', Any]) -> Dict[str, Any]:
        context_data: Dict[str, Any] = super().get_context_data(**kwargs)
        context_data['game_id'] = self.kwargs['game_id']
        return context_data

    def get_success_url(self) -> str:
        return f'/games/{self.kwargs["game_id"]}/'
