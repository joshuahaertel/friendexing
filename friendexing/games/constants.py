from datetime import timedelta

GAME_EXPIRY_DELTA = timedelta(hours=2)
GAME_EXPIRY_SECONDS = GAME_EXPIRY_DELTA.total_seconds()

NUM_TOP_PLAYERS = 3
TOP_PLAYER_INDEX = NUM_TOP_PLAYERS - 1


class MessageSeverityLevel:
    DANGER = 'danger'
    WARNING = 'warning'
    INFO = 'info'
