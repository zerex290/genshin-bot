from dataclasses import dataclass
from typing import Any


@dataclass()
class Information:
    name: str
    enemy_type: str
    drop: str
    description: str


@dataclass()
class ProgressionRow:
    level: str | Any

    one_player_hp: int | Any
    one_player_atk: int | Any
    one_player_def: int | Any

    two_player_hp: int | Any
    two_player_atk: int | Any
    two_player_def: int | Any

    three_player_hp: int | Any
    three_player_atk: int | Any
    three_player_def: int | Any

    four_player_hp: int | Any
    four_player_atk: int | Any
    four_player_def: int | Any


@dataclass()
class Progression:
    information: list[ProgressionRow]
