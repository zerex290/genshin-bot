import datetime
from dataclasses import dataclass
from typing import List


@dataclass()
class CustomCommand:
    name: str
    creator_id: int
    _date: datetime.datetime
    times_used: int
    message: str
    document_id: str
    audio_id: str
    has_photo: bool

    @property
    def date_added(self) -> datetime.datetime:
        """Command creation date with Moscow tz offset"""
        tz_offset = datetime.timedelta(hours=3)
        tz = datetime.timezone(tz_offset)
        return self._date.astimezone(tz)


@dataclass()
class ChatCustomCommands:
    chat_id: int
    _commands: List[CustomCommand]

    def __iter__(self) -> CustomCommand:
        for command in self._commands:
            yield command

    def __contains__(self, item) -> bool:
        return item in [command.name for command in self._commands]

    def __bool__(self) -> bool:
        return True if self._commands else False
