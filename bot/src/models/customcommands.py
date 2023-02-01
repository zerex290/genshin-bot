import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass()
class CustomCommand:
    name: str
    chat_id: int
    creator_id: int
    _date_added: datetime.datetime
    times_used: int
    message: str
    document_id: str
    audio_id: str
    photo_id: str
    edits_num: int
    _date_edited: Optional[datetime.datetime]
    editor_id: Optional[int]

    @property
    def date_added(self) -> datetime.datetime:
        """Command creation date with Moscow tz offset"""
        tz_offset = datetime.timedelta(hours=3)
        tz = datetime.timezone(tz_offset)
        return self._date_added.astimezone(tz)

    @property
    def date_edited(self) -> Optional[datetime.datetime]:
        """Command editing date with Moscow tz offset"""
        if self._date_edited is None:
            return None
        tz_offset = datetime.timedelta(hours=3)
        tz = datetime.timezone(tz_offset)
        return self._date_edited.astimezone(tz)
