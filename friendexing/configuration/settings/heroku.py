import ssl

from .base import *

DEBUG = False

ALLOWED_HOSTS = ['friendexing.herokuapp.com']

REDIS_CONFIGURATION = {
    'address': REDIS_URL,
    'ssl': ssl._create_unverified_context(),
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [
                REDIS_CONFIGURATION
            ],
        },
    },
}

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

_INSERT_INDEX = (
        MIDDLEWARE.index('django.middleware.security.SecurityMiddleware') + 1
)
MIDDLEWARE.insert(_INSERT_INDEX, 'whitenoise.middleware.WhiteNoiseMiddleware')

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {"level": "INFO", "handlers": ["file"]},
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "/dev/stdout",
            "formatter": "app",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": True
        },
    },
    "formatters": {
        "app": {
            "format": (
                u"%(asctime)s [%(levelname)-8s] "
                "(%(module)s.%(funcName)s) %(message)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
}
