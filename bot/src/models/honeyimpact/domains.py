from dataclasses import dataclass
from typing import Optional
from re import sub


@dataclass(frozen=True)
class Information:
    name: str
    type: str
    recommended_elements: tuple[str, ...]
    disorders: Optional[tuple[str, ...]]
    description: str


@dataclass(frozen=True)
class Monster:
    base_url: str
    src: str

    @property
    def url(self) -> str:
        return f"{self.base_url}{self.src[1:]}"

    @property
    def code(self) -> str:
        return sub(r'_35.png|_50.png', '', self.url.split('/')[-1])


@dataclass(frozen=True)
class Drop:
    base_url: str
    src: str

    @property
    def url(self) -> str:
        return f"{self.base_url}{self.src[1:]}"

    @property
    def code(self) -> str:
        return sub(r'_35.png|_50.png', '', self.url.split('/')[-1])
