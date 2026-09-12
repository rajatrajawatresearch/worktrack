from datetime import UTC, datetime, timedelta

from app.services import time_calc


class _Break:
    def __init__(self, started_at, ended_at):
        self.started_at = started_at
        self.ended_at = ended_at


def test_net_work_minutes_excludes_breaks():
    pin = datetime(2026, 9, 13, 9, 0, tzinfo=UTC)
    pout = datetime(2026, 9, 13, 18, 0, tzinfo=UTC)  # 540 gross
    breaks = [
        _Break(
            datetime(2026, 9, 13, 13, 0, tzinfo=UTC),
            datetime(2026, 9, 13, 13, 30, tzinfo=UTC),
        )
    ]
    assert time_calc.gross_minutes(pin, pout) == 540
    assert time_calc.completed_break_minutes(breaks) == 30
    assert time_calc.net_work_minutes(pin, pout, breaks) == 510


def test_current_work_minutes_with_active_break():
    pin = datetime(2026, 9, 13, 9, 0, tzinfo=UTC)
    now = pin + timedelta(minutes=120)
    # break started 60 min in and is still active (60 min so far)
    breaks = [_Break(pin + timedelta(minutes=60), None)]
    assert time_calc.current_work_minutes(pin, breaks, now) == 60


def test_break_duration_minutes():
    start = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)
    end = start + timedelta(minutes=45)
    assert time_calc.break_duration_minutes(start, end) == 45


def test_naive_datetimes_treated_as_utc():
    pin = datetime(2026, 9, 13, 9, 0)  # naive
    pout = datetime(2026, 9, 13, 10, 0)  # naive
    assert time_calc.gross_minutes(pin, pout) == 60


def test_net_work_never_negative():
    pin = datetime(2026, 9, 13, 9, 0, tzinfo=UTC)
    pout = datetime(2026, 9, 13, 9, 10, tzinfo=UTC)  # 10 min gross
    breaks = [
        _Break(
            datetime(2026, 9, 13, 9, 0, tzinfo=UTC),
            datetime(2026, 9, 13, 9, 30, tzinfo=UTC),
        )
    ]  # 30 min break > gross
    assert time_calc.net_work_minutes(pin, pout, breaks) == 0
