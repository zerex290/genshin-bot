import datetime


def get_current_timestamp(tz_offset: int) -> datetime.datetime:
    return datetime.datetime.now(tz=get_tz(tz_offset))


def get_tz(offset: int) -> datetime.timezone:
    tz_offset = datetime.timedelta(hours=offset)
    return datetime.timezone(tz_offset)
