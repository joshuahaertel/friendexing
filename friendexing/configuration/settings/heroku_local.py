from .base import *

DEBUG = False

ALLOWED_HOSTS = ['localhost']

REDIS_CONFIGURATION = {
    'address': REDIS_URL,
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [
                REDIS_CONFIGURATION,
            ],
        },
    },
}

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

_INSERT_INDEX = (
        MIDDLEWARE.index('django.middleware.security.SecurityMiddleware') + 1
)
MIDDLEWARE.insert(_INSERT_INDEX, 'whitenoise.middleware.WhiteNoiseMiddleware')
