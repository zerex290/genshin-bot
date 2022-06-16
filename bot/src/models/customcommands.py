import datetime
from dataclasses import dataclass


@dataclass()
class CustomCommand:
    chat_id: int
    name: str
    creator_id: int
    _date: datetime.datetime
    times_used: int
    message: str
    document_id: str
    audio_id: str
    photo_id: str

    @property
    def date_added(self) -> datetime.datetime:
        """Command creation date with Moscow tz offset"""
        tz_offset = datetime.timedelta(hours=3)
        tz = datetime.timezone(tz_offset)
        return self._date.astimezone(tz)
