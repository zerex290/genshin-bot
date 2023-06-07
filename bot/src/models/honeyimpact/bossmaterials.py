from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class BossMaterial:
    icon: str
    used_by: List[str]


@dataclass(frozen=True)
class Boss:
    icon: str
    materials: List[BossMaterial]
