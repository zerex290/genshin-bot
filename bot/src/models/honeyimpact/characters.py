from dataclasses import dataclass


@dataclass()
class Information:
    name: str
    title: str
    allegiance: str
    rarity: int
    weapon: str
    element: str
    ascension_stat: str
    birthday: str
    astrolabe_name: str
    description: str


@dataclass()
class Skill:
    title: str
    description: str

