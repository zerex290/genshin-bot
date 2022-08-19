from dataclasses import dataclass


@dataclass(frozen=True)
class Information:
    name: str
    weapon_type: str
    rarity: int
    primary_stat_title: str
    primary_stat_value: float
    secondary_stat_title: str
    secondary_stat_value: int | float | str
    description: str


@dataclass(frozen=True)
class Ability:
    title: str
    description: str


@dataclass(frozen=True)
class Progression:
    level: int | str
    primary_stat_title: str
    primary_stat_value: int | float | str
    secondary_stat_title: str
    secondary_stat_value: int | float | str


@dataclass(frozen=True)
class Refinement:
    level: str
    description: str
