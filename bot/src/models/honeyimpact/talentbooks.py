from dataclasses import dataclass

from ...types.uncategorized import Weekday


@dataclass(frozen=True)
class TalentBook:
    icon: str
    weekdays: list[Weekday]
    used_by: list[str]
