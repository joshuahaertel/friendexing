from typing import List, Dict
from uuid import UUID


class Game:
    id: UUID
    settings: 'Settings'
    players: List['Player']
    batches: List['Batch']
    state: str


class Settings:
    max_time_to_guess: int
    should_randomize_fields: bool


class Player:
    id: UUID
    name: str
    score: int
    guess_id: int
    guess: str
    guess_time: int


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
