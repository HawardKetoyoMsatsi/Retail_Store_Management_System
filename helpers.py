"""Small shared helpers: validation and dates."""
import calendar
import re
from datetime import date, timedelta

from config import STOCK_TAKE_WEEKDAY


class BadRequest(Exception):
    """Raised for input the user can fix; shown to them as a message."""


def num(v, name="value", allow_blank=True):
    if v is None or str(v).strip() == "":
        if allow_blank:
            return 0.0
        raise BadRequest(f"{name} is required")
    try:
        n = float(v)
    except ValueError:
        raise BadRequest(f"{name} must be a number")
    if n < 0:
        raise BadRequest(f"{name} cannot be negative")
    return n


def check_date(d):
    if not d or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(d)):
        raise BadRequest("Pick a valid date")
    try:
        date.fromisoformat(d)
    except ValueError:
        raise BadRequest("Pick a valid date")
    return d


def today():
    return date.today().isoformat()


# ---- stock take day (Sunday by default; change STOCK_TAKE_WEEKDAY in config.py)
STOCK_DAY_NAME = calendar.day_name[STOCK_TAKE_WEEKDAY]


def is_stock_day(d):
    return date.fromisoformat(d).weekday() == STOCK_TAKE_WEEKDAY


def last_stock_day(d=None):
    """The most recent stock take day on or before d (today if d is not given)."""
    day = date.fromisoformat(d) if d else date.today()
    return (day - timedelta(days=(day.weekday() - STOCK_TAKE_WEEKDAY) % 7)).isoformat()


def next_stock_day(d=None):
    """The first stock take day strictly after d (today if d is not given)."""
    day = date.fromisoformat(d) if d else date.today()
    return (day + timedelta(days=(STOCK_TAKE_WEEKDAY - day.weekday()) % 7 or 7)).isoformat()
