from dataclasses import dataclass


@dataclass(frozen=True)
class Information:
    name: str
    title: str
    occupation: str
    association: str
    rarity: int
    weapon: str
    element: str
    ascension_stat: str
    birthdate: str
    constellation: str
    description: str


@dataclass(frozen=True)
class Skill:
    title: str
    description: str
