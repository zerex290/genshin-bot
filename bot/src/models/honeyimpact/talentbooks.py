from dataclasses import dataclass
from typing import List

from ...types.uncategorized import Weekday


@dataclass(frozen=True)
class TalentBook:
    icon: str
    weekdays: List[Weekday]
    used_by: List[str]
