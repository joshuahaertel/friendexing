from typing import List, Dict, Optional
from uuid import uuid4, UUID


class Game:

    def __init__(
            self,
            total_time_to_guess: int,
            should_randomize_fields: bool,
            name: str,
    ):
        self.id = uuid4()
        self.settings = Settings(
            total_time_to_guess,
            should_randomize_fields,
        )
        admin = Player(name)
        self.players: List['Player'] = [admin]
        self.batches: List['Batch'] = []
        self.info = Info(
            state='wait',
            admin_id=admin.id,
        )


class Settings:
    def __init__(
            self,
            total_time_to_guess: int,
            should_randomize_fields: bool,
    ):
        self.total_time_to_guess = total_time_to_guess
        self.should_randomize_fields = should_randomize_fields


class Player:
    def __init__(
            self,
            name: str,
    ):
        self.id = uuid4()
        self.name: str = name
        self.score = 0
        self.guess_id: Optional[int] = None
        self.guess: Optional[str] = None
        self.guess_time: Optional[int] = None


class Batch:
    id: UUID
    images: List['Image']
    schema: Dict[str, type]


class Image:
    id: UUID
    indexable: bool
    records: List['Record']


class Record:
    id: UUID
    fields: Dict[str, 'Field']


class Field:
    id: UUID
    value: str
    is_checked: bool


class Info:
    def __init__(
            self,
            state,
            admin_id,
    ):
        self.state = state
        self.admin_id = admin_id
