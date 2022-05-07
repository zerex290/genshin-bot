from dataclasses import dataclass
from typing import List, Any


@dataclass()
class Information:
    name: str | Any
    weapon_type: str | Any
    rarity: int | Any
    primary_stat_title: str | Any
    primary_stat_value: int | Any
    secondary_stat_title: str | Any
    secondary_stat_value: float | Any
    description: str | Any


@dataclass()
class Ability:
    title: str | Any
    description: str | Any


@dataclass()
class ProgressionRow:
    level: str | Any
    primary_stat_title: str | Any
    primary_stat_value: int | Any
    secondary_stat_title: str | Any
    secondary_stat_value: float | Any


@dataclass()
class Progression:
    information: List[ProgressionRow]
