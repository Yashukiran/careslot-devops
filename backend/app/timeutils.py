import os
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

CLINIC_TZ = ZoneInfo(os.getenv("CLINIC_TZ", "Asia/Kolkata"))


def to_utc(dt: datetime) -> datetime:
    """Store everything in UTC. Naive values are treated as clinic local time."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=CLINIC_TZ)
    return dt.astimezone(timezone.utc)


def as_naive_utc(dt: datetime) -> datetime:
    # sqlite gives back naive datetimes, postgres gives aware ones - compare them the same way
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def day_range_utc(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=CLINIC_TZ)
    return to_utc(start), to_utc(start + timedelta(days=1))


def today_local() -> date:
    return datetime.now(CLINIC_TZ).date()
