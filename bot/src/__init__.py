from typing import TypeAlias


__all__ = (
    'Options',
    'Payload',
)


Options: TypeAlias = list[str]
Payload: TypeAlias = dict[str, str | int]
