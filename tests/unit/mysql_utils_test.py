import pytest
from packaging.version import Version

from sqlite3_to_mysql.mysql_utils import (
    check_mysql_fulltext_support,
    check_mysql_json_support,
    check_mysql_values_alias_support,
    get_mysql_version,
    safe_identifier_length,
)


class TestMySQLUtils:
    @pytest.mark.parametrize(
        "version_string,expected",
        [
            ("5.7.7", Version("5.7.7")),
            ("5.7.8", Version("5.7.8")),
            ("8.0.0", Version("8.0.0")),
            ("9.0.0", Version("9.0.0")),
            ("10.2.6-mariadb", Version("10.2.6")),
            ("10.2.7-mariadb", Version("10.2.7")),
            ("11.4.0-mariadb", Version("11.4.0")),
        ],
    )
    def test_get_mysql_version(self, version_string: str, expected: Version) -> None:
        assert get_mysql_version(version_string) == expected

    @pytest.mark.parametrize(
        "version_string,expected",
        [
            ("5.7.7", False),
            ("5.7.8", True),
            ("8.0.0", True),
            ("9.0.0", True),
            ("10.2.6-mariadb", False),
            ("10.2.7-mariadb", True),
            ("11.4.0-mariadb", True),
        ],
    )
    def test_check_mysql_json_support(self, version_string: str, expected: bool) -> None:
        assert check_mysql_json_support(version_string) == expected

    @pytest.mark.parametrize(
        "version_string,expected",
        [
            ("5.7.8", False),
            ("8.0.0", False),
            ("8.0.18", False),
            ("8.0.19", True),
            ("9.0.0", True),
            ("10.2.6-mariadb", False),
            ("10.2.7-mariadb", False),
            ("11.4.0-mariadb", False),
        ],
    )
    def test_check_mysql_values_alias_support(self, version_string: str, expected: bool) -> None:
        assert check_mysql_values_alias_support(version_string) == expected

    @pytest.mark.parametrize(
        "version_string,expected",
        [
            ("5.0.0", False),
            ("5.5.0", False),
            ("5.6.0", True),
            ("8.0.0", True),
            ("10.0.4-mariadb", False),
            ("10.0.5-mariadb", True),
            ("10.2.6-mariadb", True),
            ("11.4.0-mariadb", True),
        ],
    )
    def test_check_mysql_fulltext_support(self, version_string: str, expected: bool) -> None:
        assert check_mysql_fulltext_support(version_string) == expected

    @pytest.mark.parametrize(
        "identifier,expected",
        [
            ("a" * 67, "a" * 64),
            ("a" * 66, "a" * 64),
            ("a" * 65, "a" * 64),
            ("a" * 64, "a" * 64),
            ("a" * 63, "a" * 63),
        ],
    )
    def test_safe_identifier_length(self, identifier: str, expected: str) -> None:
        assert safe_identifier_length(identifier) == expected
