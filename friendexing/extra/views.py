import os
import signal
from threading import Thread
from time import sleep

from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponseBase


def kill_server_view(_: WSGIRequest) -> HttpResponseBase:
    process_id = os.getpid()
    thread = Thread(target=kill_soon, args=(process_id,))
    thread.start()
    return HttpResponseBase()


def kill_soon(process_id: int) -> None:
    sleep(5)
    os.kill(process_id, signal.SIGINT)
