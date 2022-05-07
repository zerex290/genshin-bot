import json
from os import sep

from bot.config.dependencies.paths import FILECACHE


def dump(obj: dict, filetype: str) -> None:
    with open(FILECACHE + sep + filetype + '.json', 'w') as file:
        json.dump(obj, file)


def load(filetype: str) -> dict:
    with open(FILECACHE + sep + filetype + '.json', 'r') as file:
        return json.load(file)
