from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from dateutil.parser import ParserError
from packaging.version import Version

from sqlite3_to_mysql.sqlite_utils import (
    adapt_decimal,
    adapt_timedelta,
    check_sqlite_table_xinfo_support,
    convert_date,
    convert_decimal,
    convert_timedelta,
    unicase_compare,
)


class TestSQLiteUtils:
    def test_adapt_decimal(self) -> None:
        """Test adapt_decimal function."""
        assert adapt_decimal(Decimal("123.45")) == "123.45"
        assert adapt_decimal(Decimal("0")) == "0"
        assert adapt_decimal(Decimal("-123.45")) == "-123.45"

    def test_convert_decimal(self) -> None:
        """Test convert_decimal function."""
        assert convert_decimal(b"123.45") == Decimal("123.45")
        assert convert_decimal(b"0") == Decimal("0")
        assert convert_decimal(b"-123.45") == Decimal("-123.45")

    def test_adapt_timedelta(self) -> None:
        """Test adapt_timedelta function."""
        assert adapt_timedelta(timedelta(hours=1, minutes=30, seconds=45)) == "01:30:45"
        assert adapt_timedelta(timedelta(hours=0, minutes=0, seconds=0)) == "00:00:00"
        assert adapt_timedelta(timedelta(hours=100, minutes=30, seconds=45)) == "100:30:45"

    def test_convert_timedelta(self) -> None:
        """Test convert_timedelta function."""
        assert convert_timedelta(b"01:30:45") == timedelta(hours=1, minutes=30, seconds=45)
        assert convert_timedelta(b"00:00:00") == timedelta(hours=0, minutes=0, seconds=0)
        assert convert_timedelta(b"100:30:45") == timedelta(hours=100, minutes=30, seconds=45)

    def test_unicase_compare(self) -> None:
        """Test unicase_compare function."""
        # Test with lowercase strings
        assert unicase_compare("abc", "def") == -1
        assert unicase_compare("def", "abc") == 1
        assert unicase_compare("abc", "abc") == 0

        # Test with mixed case strings
        assert unicase_compare("Abc", "def") == -1
        assert unicase_compare("DEF", "abc") == 1
        assert unicase_compare("ABC", "abc") == 0

        # Test with accented characters
        assert unicase_compare("café", "cafe") == 0
        assert unicase_compare("café", "cafz") == -1
        assert unicase_compare("cafz", "café") == 1

    def test_convert_date(self) -> None:
        """Test convert_date function."""
        # Test with string
        assert convert_date("2020-01-01") == date(2020, 1, 1)
        assert convert_date("2020/01/01") == date(2020, 1, 1)
        assert convert_date("Jan 1, 2020") == date(2020, 1, 1)

        # Test with bytes
        assert convert_date(b"2020-01-01") == date(2020, 1, 1)
        assert convert_date(b"2020/01/01") == date(2020, 1, 1)
        assert convert_date(b"Jan 1, 2020") == date(2020, 1, 1)

    def test_convert_date_error(self) -> None:
        """Test convert_date function with invalid date."""
        with pytest.raises(ValueError):
            convert_date("not a date")

        with pytest.raises(ValueError):
            convert_date(b"not a date")

    @pytest.mark.parametrize(
        "version_string,expected",
        [
            ("3.25.0", False),
            ("3.26.0", True),
            ("3.27.0", True),
            ("4.0.0", True),
        ],
    )
    def test_check_sqlite_table_xinfo_support(self, version_string: str, expected: bool) -> None:
        """Test check_sqlite_table_xinfo_support function."""
        assert check_sqlite_table_xinfo_support(version_string) == expected
