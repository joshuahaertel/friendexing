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
        self.state = State(
            phase='wait',
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
            id_=None,
            score=0,
            guess_id='',
            guess='',
            potential_points=0,
    ):
        self.id = id_ or uuid4()
        self.name: str = name
        self.score = score
        # todo: need this?
        self.guess_id: str = guess_id
        self.guess: str = guess
        self.potential_points: int = potential_points


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


class State:
    def __init__(
            self,
            phase,
            admin_id,
    ):
        self.phase = phase
        self.admin_id = admin_id
        self.guess_end_time: Optional[float] = None
