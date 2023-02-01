from dataclasses import dataclass


@dataclass(frozen=True)
class BossMaterial:
    icon: str
    used_by: list[str]


@dataclass(frozen=True)
class Boss:
    icon: str
    materials: list[BossMaterial]
