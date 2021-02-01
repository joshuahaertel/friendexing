from typing import List, Dict, Optional
from uuid import UUID, uuid4


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
        self.players: List['Player'] = [
            Player(
                name,
            ),
        ]
        self.batches: List['Batch'] = []
        self.state = 'wait'


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
    images: List['Image']
    schema: Dict[str, type]


class Image:
    indexable: bool
    records: List['Record']


class Record:
    fields: Dict[str, 'Field']


class Field:
    value: str
    is_checked: bool
