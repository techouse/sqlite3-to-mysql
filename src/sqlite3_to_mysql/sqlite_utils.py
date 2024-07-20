"""SQLite adapters and converters for unsupported data types."""

import typing as t
from datetime import date, timedelta
from decimal import Decimal

from dateutil.parser import ParserError
from dateutil.parser import parse as dateutil_parse
from packaging import version
from packaging.version import Version
from pytimeparse2 import parse
from unidecode import unidecode


def adapt_decimal(value) -> str:
    """Convert decimal.Decimal to string."""
    return str(value)


def convert_decimal(value) -> Decimal:
    """Convert string to decimalDecimal."""
    return Decimal(str(value.decode()))


def adapt_timedelta(value) -> str:
    """Convert datetime.timedelta to %H:%M:%S string."""
    hours, remainder = divmod(value.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    return "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))


def convert_timedelta(value) -> timedelta:
    """Convert %H:%M:%S string to datetime.timedelta."""
    return timedelta(seconds=parse(value.decode()))


def unicase_compare(string_1: str, string_2: str) -> int:
    """Taken from https://github.com/patarapolw/ankisync2/issues/3#issuecomment-768687431."""
    _string_1: str = unidecode(string_1).lower()
    _string_2: str = unidecode(string_2).lower()
    return 1 if _string_1 > _string_2 else -1 if _string_1 < _string_2 else 0


def convert_date(value: t.Union[str, bytes]) -> date:
    """Handle SQLite date conversion."""
    try:
        return dateutil_parse(value.decode() if isinstance(value, bytes) else value).date()
    except ParserError as err:
        raise ValueError(f"DATE field contains {err}")  # pylint: disable=W0707


def check_sqlite_table_xinfo_support(version_string: str) -> bool:
    """Check for SQLite table_xinfo support."""
    sqlite_version: Version = version.parse(version_string)
    return sqlite_version.major > 3 or (sqlite_version.major == 3 and sqlite_version.minor >= 26)
