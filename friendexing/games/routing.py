from django.urls import path

from games.consumers import PlayConsumer, AdminConsumer, AConsumer

websocket_urlpatterns = [
    path('ws/play/<uuid:game_id>/<uuid:player_id>/', PlayConsumer.as_asgi()),
    path('ws/play/<str:game_id>/<str:player_id>/', PlayConsumer.as_asgi()),
    path('ws/admin/<uuid:game_id>/', AdminConsumer.as_asgi()),
    path('ws/dumb/', AConsumer.as_asgi()),
]
