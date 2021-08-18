"""
ASGI config for configuration project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

from games.consumers import ImageConsumer
from games.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configuration.settings.base')

application = ProtocolTypeRouter({
    'http': URLRouter([
        path('images', ImageConsumer.as_asgi()),
        path('<path:path>', get_asgi_application()),
    ]),
    'websocket': URLRouter(
        websocket_urlpatterns
    ),
})
