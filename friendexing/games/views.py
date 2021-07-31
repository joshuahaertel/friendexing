from datetime import timedelta, datetime
from typing import Optional, Any, Dict
from uuid import UUID

from django.forms import BaseForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_protect
from django.views.generic import FormView

from games.forms import GameForm, PlayerForm
from games.models import Game


def get_expiry() -> datetime:
    return now() + timedelta(hours=2)


class GameCreate(FormView):
    template_name = 'games/create.html'  # noqa: F841
    form_class = GameForm  # noqa: F841
    game: Optional[Game] = None

    def form_valid(self, form: BaseForm) -> HttpResponse:
        assert isinstance(form, GameForm)
        self.game = form.create_game()
        response = super().form_valid(form)
        response.set_cookie(
            key=str(self.game.id),
            value=str(self.game.players[0].id),
            expires=get_expiry(),
        )
        return response

    def get_success_url(self) -> str:
        assert self.game
        return f'/games/{self.game.id}/'


@csrf_protect
def game_view(request: HttpRequest, game_id: UUID) -> HttpResponse:
    game_id_str = str(game_id)
    player_id = request.COOKIES.get(game_id_str)
    if player_id:
        if request.GET.get('isAdmin', '') == '1':
            response = render(request, 'games/admin.html')
        else:
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
        response.set_cookie(
            key=str(self.kwargs['game_id']),
            value=str(player.id),
            expires=get_expiry(),
        )
        return response

    def get_context_data(self, **kwargs: Dict['str', Any]) -> Dict[str, Any]:
        context_data: Dict[str, Any] = super().get_context_data(**kwargs)
        context_data['game_id'] = self.kwargs['game_id']
        return context_data

    def get_success_url(self) -> str:
        return f'/games/{self.kwargs["game_id"]}/'
