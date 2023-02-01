from dataclasses import dataclass


@dataclass(frozen=True)
class Information:
    name: str
    type: str
    rarity: str
    affix: list[str]
