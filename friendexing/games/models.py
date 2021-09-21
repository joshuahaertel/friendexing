from typing import List, Optional
from uuid import uuid4


class Game:

    def __init__(
            self,
            total_time_to_guess: int,
            should_randomize_fields: bool,
            name: str,
    ):
        self.id = uuid4()
        admin = Player(name)
        self.players: List['Player'] = [admin]
        self.batches: List['Batch'] = []
        self.state = State(
            total_time_to_guess,
            should_randomize_fields,
            phase='wait',
            admin_id=admin.id,
        )


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

    def __init__(
            self,
            id_: str,
            image_models: List['ImageModel'],
    ):
        self.id = id_
        self.image_models = image_models


class ImageModel:

    def __init__(
            self,
            id_: str,
            image_bytes: bytes,
            thumbnail_bytes: bytes,
    ):
        self.id = id_
        self.image_bytes = image_bytes
        self.thumbnail_bytes = thumbnail_bytes


class TemplateField:
    def __init__(
            self,
            image_id: str,
            label: str,
            display_name: str,
            required: bool,
            help_text: str,
            alpha_type: str,  # todo: enum
            max_length: Optional[int],
            max_value: Optional[int],
            min_length: Optional[int],
            min_value: Optional[int],
            auto_capitalization: Optional[bool],
            symbol: Optional[str],
            acceptable_values: Optional[List[str]],
    ) -> None:
        self.image_id = image_id
        self.label = label
        self.display_name = display_name
        self.required = required
        self.help_text = help_text
        self.alpha_type = alpha_type
        self.max_length = max_length
        self.max_value = max_value
        self.min_length = min_length
        self.min_value = min_value
        self.auto_capitalization = auto_capitalization
        self.symbol = symbol
        self.acceptable_values = acceptable_values


class State:
    def __init__(
            self,
            total_time_to_guess: int,
            should_randomize_fields: bool,
            phase,
            admin_id,
            guess_end_time=0,
    ):
        self.total_time_to_guess = total_time_to_guess
        self.should_randomize_fields = should_randomize_fields
        self.phase = phase
        self.admin_id = admin_id
        self.guess_end_time: float = guess_end_time


class Phases:
    PLAY = 'play'
    WAIT = 'wait'
