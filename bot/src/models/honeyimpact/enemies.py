from dataclasses import dataclass
from typing import Union, Dict


@dataclass(frozen=True)
class Information:
    name: str
    enemy_type: str
    grade: str
    drop: Dict[str, str]
    description: str


@dataclass(frozen=True)
class Progression:
    level: Union[int, str]

    one_player_hp: Union[int, float, str]
    one_player_atk: Union[int, float, str]
    one_player_def: Union[int, float, str]

    two_player_hp: Union[int, float, str]
    two_player_atk: Union[int, float, str]
    two_player_def: Union[int, float, str]

    three_player_hp: Union[int, float, str]
    three_player_atk: Union[int, float, str]
    three_player_def: Union[int, float, str]

    four_player_hp: Union[int, float, str]
    four_player_atk: Union[int, float, str]
    four_player_def: Union[int, float, str]
