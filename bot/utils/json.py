import json
from os import sep

from ..config.dependencies.paths import FILECACHE


def dump(obj: dict, filetype: str) -> None:
    if obj:
        with open(FILECACHE + sep + filetype + '.json', 'w') as file:
            json.dump(obj, file, indent=4, ensure_ascii=False)


def load(filetype: str) -> dict:
    with open(FILECACHE + sep + filetype + '.json', 'r') as file:
        return json.load(file)
