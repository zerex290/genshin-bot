from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    weekday: int
    icon: str


@dataclass(frozen=True)
class Consumer:
    title: str
    weekdays: list[int]
    icon: str
    rarity: int


@dataclass(frozen=True)
class Zone:
    title: str
    materials: list[Material]
    consumers: list[Consumer]
