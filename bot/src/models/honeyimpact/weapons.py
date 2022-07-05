from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Information:
    name: str | Any
    weapon_type: str | Any
    rarity: int | Any
    primary_stat_title: str | Any
    primary_stat_value: int | Any
    secondary_stat_title: str | Any
    secondary_stat_value: float | Any
    description: str | Any


@dataclass(frozen=True)
class Ability:
    title: str | Any
    description: str | Any


@dataclass(frozen=True)
class Progression:
    level: str | Any
    primary_stat_title: str | Any
    primary_stat_value: int | Any
    secondary_stat_title: str | Any
    secondary_stat_value: float | Any


@dataclass(frozen=True)
class Refinement:
    level: str | Any
    description: str | Any
