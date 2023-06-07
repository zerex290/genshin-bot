from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Information:
    name: str
    type: str
    rarity: int
    primary_stat_title: str
    primary_stat_value: float
    secondary_stat_title: str
    secondary_stat_value: Union[int, float, str]
    description: str


@dataclass(frozen=True)
class Ability:
    title: str
    description: str


@dataclass(frozen=True)
class Progression:
    level: Union[int, str]
    primary_stat_title: str
    primary_stat_value: Union[int, float, str]
    secondary_stat_title: str
    secondary_stat_value: Union[int, float, str]


@dataclass(frozen=True)
class Refinement:
    level: str
    description: str
