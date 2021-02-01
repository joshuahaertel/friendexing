from django.urls import path

from games.views import GameCreate, game_view, PlayerCreate

urlpatterns = [
    path('<uuid:game_id>/', game_view),
    path('<uuid:game_id>/join/', PlayerCreate.as_view()),
    path('create/', GameCreate.as_view()),
]
