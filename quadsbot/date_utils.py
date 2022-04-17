import pytz
from datetime import datetime

# Formats the date as a series of human readable numbers
# 2020-10-22T12:51:24 -> 20201022125124
# NOTE: Must be in 24 -> 12 hour order for the check_id below
format_strings = [
    "%Y%m%d%H%M%S",  # 24 hour
    "%Y%m%d%I%M%S",  # 12 hour
]


def get_date_strings(date: datetime, tz: str) -> list[int]:
    # Convert date to bot timezone
    date = date.astimezone(pytz.timezone(tz))

    return [date.strftime(format_string) for format_string in format_strings]


def is_april_fools_day(date: datetime, tz) -> bool:
    now = date.astimezone(pytz.timezone(tz))
    return now.month == 4 and now.day == 1
