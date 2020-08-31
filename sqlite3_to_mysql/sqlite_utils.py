"""SQLite adapters and converters for unsupported data types."""

from __future__ import division

from datetime import timedelta
from decimal import Decimal

import six
from pytimeparse.timeparse import timeparse


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
