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


@dataclass(frozen=True)
class AscensionMaterial:
    icon: str
    quantity: int


@dataclass(frozen=True)
class Ascension:
    gacha_icon: str
    lvl: list[AscensionMaterial]
    talents: list[AscensionMaterial]
