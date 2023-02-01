from dataclasses import dataclass


@dataclass(frozen=True)
class Information:
    name: str
    enemy_type: str
    grade: str
    drop: dict[str, str]
    description: str


@dataclass(frozen=True)
class Progression:
    level: int | str

    one_player_hp: int | float | str
    one_player_atk: int | float | str
    one_player_def: int | float | str

    two_player_hp: int | float | str
    two_player_atk: int | float | str
    two_player_def: int | float | str

    three_player_hp: int | float | str
    three_player_atk: int | float | str
    three_player_def: int | float | str

    four_player_hp: int | float | str
    four_player_atk: int | float | str
    four_player_def: int | float | str
