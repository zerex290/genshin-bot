from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Information:
    name: str
    type: str
    rarity: str
    affix: List[str]
