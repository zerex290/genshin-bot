from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Material:
    weekday: int
    icon: str


@dataclass(frozen=True)
class Consumer:
    title: str
    weekdays: List[int]
    icon: str
    rarity: int


@dataclass(frozen=True)
class Zone:
    title: str
    materials: List[Material]
    consumers: List[Consumer]
