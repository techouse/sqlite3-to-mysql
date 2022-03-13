"""SQLite adapters and converters for unsupported data types."""

from __future__ import division

from datetime import date, datetime, timedelta
from decimal import Decimal
from sys import version_info

import six
from pytimeparse.timeparse import timeparse
from unidecode import unidecode

if version_info.major == 3 and 4 <= version_info.minor <= 6:
    from backports.datetime_fromisoformat import MonkeyPatch  # pylint: disable=E0401

    MonkeyPatch.patch_fromisoformat()


def adapt_decimal(value):
    """Convert decimal.Decimal to string."""
    return str(value)


def convert_decimal(value):
    """Convert string to decimalDecimal."""
    return Decimal(str(value.decode()))


def adapt_timedelta(value):
    """Convert datetime.timedelta to %H:%M:%S string."""
    hours, remainder = divmod(value.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    return "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))


def convert_timedelta(value):
    """Convert %H:%M:%S string to datetime.timedelta."""
    return timedelta(seconds=timeparse(value.decode()))


def convert_blob(value):
    """In Python 2 MySQL binary protocol can not handle 'buffer' objects so we have to convert them."""
    return six.binary_type(value)


def unicase_compare(string_1, string_2):
    """Taken from https://github.com/patarapolw/ankisync2/issues/3#issuecomment-768687431."""
    _string_1 = unidecode(string_1).lower()
    _string_2 = unidecode(string_2).lower()
    return 1 if _string_1 > _string_2 else -1 if _string_1 < _string_2 else 0


def convert_date(value):
    """Handle SQLite date conversion."""
    if six.PY3:
        try:
            return date.fromisoformat(value.decode())
        except ValueError as err:
            raise ValueError(  # pylint: disable=W0707
                "DATE field contains {}".format(err)
            )
    try:
        return datetime.strptime(value.decode(), "%Y-%m-%d").date()
    except ValueError as err:
        raise ValueError(  # pylint: disable=W0707
            "DATE field contains Invalid isoformat string: {}".format(err)
        )
