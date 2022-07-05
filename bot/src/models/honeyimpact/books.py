from dataclasses import dataclass


@dataclass(frozen=True)
class Information:
    name: str
    volume: str
    story: str
