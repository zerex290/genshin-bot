from typing import Any
from dataclasses import dataclass


@dataclass()
class Information:
    name: str
    artifact_type: str
    rarity: str
    two_piece_bonus: str | Any
    four_piece_bonus: str | Any