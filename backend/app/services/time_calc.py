"""Working-time calculations. Server timestamps are the source of truth."""

from collections.abc import Iterable
from datetime import datetime, timezone


def _aware(dt: datetime) -> datetime:
    """Treat naive datetimes (possible on SQLite) as UTC."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _minutes_between(start: datetime, end: datetime) -> float:
    return (_aware(end) - _aware(start)).total_seconds() / 60.0


def completed_break_minutes(breaks: Iterable) -> int:
    total = 0.0
    for b in breaks:
        if b.started_at and b.ended_at:
            total += _minutes_between(b.started_at, b.ended_at)
    return int(round(total))


def active_break_minutes(breaks: Iterable, now: datetime) -> int:
    for b in breaks:
        if b.started_at and not b.ended_at:
            return int(round(_minutes_between(b.started_at, now)))
    return 0


def gross_minutes(punch_in: datetime, end: datetime) -> int:
    return int(round(_minutes_between(punch_in, end)))


def net_work_minutes(punch_in: datetime, punch_out: datetime, breaks: Iterable) -> int:
    gross = gross_minutes(punch_in, punch_out)
    return max(0, gross - completed_break_minutes(breaks))


def current_work_minutes(punch_in: datetime, breaks: Iterable, now: datetime) -> int:
    """Live net working minutes for an in-progress day (excludes all break time)."""
    gross = gross_minutes(punch_in, now)
    excluded = completed_break_minutes(breaks) + active_break_minutes(breaks, now)
    return max(0, gross - excluded)


def break_duration_minutes(start: datetime, end: datetime) -> int:
    return max(0, int(round(_minutes_between(start, end))))
