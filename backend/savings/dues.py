"""Due dates for savings groups.

Monthly groups are due on `due_day` each month. Weekly groups are due every
7 days on the weekday they started. Gold for a period's contributions is bought
on its due date (DESIGN.md section 9).
"""

import calendar
from datetime import date, timedelta

from django.utils import timezone


def today():
    return timezone.localdate()


def _monthly(year, month, day):
    return date(year, month, min(day, calendar.monthrange(year, month)[1]))


def _add_months(d, n, day):
    m = d.month - 1 + n
    return _monthly(d.year + m // 12, m % 12 + 1, day)


def next_due(group, on=None):
    """The first due date on or after `on`."""
    on = on or today()
    if group.frequency == group.Frequency.WEEKLY:
        anchor = group.started_at or on
        return on + timedelta(days=(anchor.weekday() - on.weekday()) % 7)
    this_month = _monthly(on.year, on.month, group.due_day)
    return this_month if on <= this_month else _add_months(on, 1, group.due_day)


def last_due(group, on=None):
    """The most recent due date on or before `on`."""
    on = on or today()
    if group.frequency == group.Frequency.WEEKLY:
        anchor = group.started_at or on
        return on - timedelta(days=(on.weekday() - anchor.weekday()) % 7)
    this_month = _monthly(on.year, on.month, group.due_day)
    return this_month if on >= this_month else _add_months(on, -1, group.due_day)


def period_start(group, on=None):
    """First day of the current payment period (the day after the previous due date)."""
    on = on or today()
    due = next_due(group, on)
    if group.frequency == group.Frequency.WEEKLY:
        return due - timedelta(days=6)
    return _add_months(due, -1, group.due_day) + timedelta(days=1)


def periods_elapsed(group, on=None):
    """How many due dates have passed since the group started (0 before the first)."""
    if not group.started_at:
        return 0
    on = on or today()
    count, d = 0, next_due(group, group.started_at)
    while d < on and count < 1000:
        count += 1
        d = d + timedelta(days=7) if group.frequency == group.Frequency.WEEKLY else _add_months(d, 1, group.due_day)
    return count


def maturity_date(group):
    """Annuity: the due date of its last period."""
    if not group.started_at:
        return None
    first = next_due(group, group.started_at)
    n = group.term_cycles - 1
    if group.frequency == group.Frequency.WEEKLY:
        return first + timedelta(days=7 * n)
    return _add_months(first, n, group.due_day)
