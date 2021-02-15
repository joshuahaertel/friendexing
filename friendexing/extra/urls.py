from django.urls import path

from extra.views import kill_server_view

urlpatterns = [
    path('kill-server/', kill_server_view),
]
