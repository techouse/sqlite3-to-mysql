from unittest.mock import MagicMock, patch

import pytest
from packaging.version import Version

from sqlite3_to_mysql.mysql_utils import (
    CharSet,
    check_mysql_current_timestamp_datetime_support,
    check_mysql_expression_defaults_support,
    check_mysql_fractional_seconds_support,
    check_mysql_fulltext_support,
    check_mysql_json_support,
    check_mysql_values_alias_support,
    get_mysql_version,
    mysql_supported_character_sets,
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

    def test_mysql_supported_character_sets_with_charset(self) -> None:
        """Test mysql_supported_character_sets function with a specific charset."""
        # Mock the MYSQL_CHARACTER_SETS list
        mock_character_sets = [
            None,  # Index 0
            ("utf8", "utf8_general_ci", True),  # Index 1
            ("latin1", "latin1_swedish_ci", True),  # Index 2
        ]

        with patch("sqlite3_to_mysql.mysql_utils.MYSQL_CHARACTER_SETS", mock_character_sets):
            # Test with a charset that exists
            result = list(mysql_supported_character_sets(charset="utf8"))
            assert len(result) == 1
            assert result[0] == CharSet(1, "utf8", "utf8_general_ci")

            # Test with a charset that doesn't exist
            result = list(mysql_supported_character_sets(charset="unknown"))
            assert len(result) == 0

    def test_mysql_supported_character_sets_without_charset(self) -> None:
        """Test mysql_supported_character_sets function without a specific charset."""
        # Mock the MYSQL_CHARACTER_SETS list
        mock_character_sets = [
            None,  # Index 0
            ("utf8", "utf8_general_ci", True),  # Index 1
            ("latin1", "latin1_swedish_ci", True),  # Index 2
        ]

        # Mock the CharacterSet().get_supported() method
        mock_get_supported = MagicMock(return_value=["utf8", "latin1"])

        with patch("sqlite3_to_mysql.mysql_utils.MYSQL_CHARACTER_SETS", mock_character_sets):
            with patch("mysql.connector.CharacterSet.get_supported", mock_get_supported):
                result = list(mysql_supported_character_sets())
                # The function yields a CharSet for each combination of charset and index
                assert len(result) == 4
                assert CharSet(1, "utf8", "utf8_general_ci") in result
                assert CharSet(2, "utf8", "latin1_swedish_ci") in result
                assert CharSet(1, "latin1", "utf8_general_ci") in result
                assert CharSet(2, "latin1", "latin1_swedish_ci") in result

    def test_mysql_supported_character_sets_with_keyerror(self) -> None:
        """Test mysql_supported_character_sets function with KeyError."""
        # Mock the MYSQL_CHARACTER_SETS list with an entry that will cause a KeyError
        mock_character_sets = [
            None,  # Index 0
            ("utf8", "utf8_general_ci", True),  # Index 1
            None,  # Index 2 - This will cause a KeyError when accessed
        ]

        with patch("sqlite3_to_mysql.mysql_utils.MYSQL_CHARACTER_SETS", mock_character_sets):
            # Test with a charset that exists but will cause a KeyError
            result = list(mysql_supported_character_sets(charset="utf8"))
            assert len(result) == 1
            assert result[0] == CharSet(1, "utf8", "utf8_general_ci")

        # Mock for testing without charset
        mock_get_supported = MagicMock(return_value=["utf8"])

        with patch("sqlite3_to_mysql.mysql_utils.MYSQL_CHARACTER_SETS", mock_character_sets):
            with patch("mysql.connector.CharacterSet.get_supported", mock_get_supported):
                result = list(mysql_supported_character_sets())
                assert len(result) == 1
                assert CharSet(1, "utf8", "utf8_general_ci") in result

    def test_mysql_supported_character_sets_with_keyerror_in_info_access(self) -> None:
        """Test mysql_supported_character_sets function with KeyError when accessing info elements."""

        # Create a mock tuple that will raise KeyError when accessed with index
        class MockTuple:
            def __getitem__(self, key):
                if key == 0:
                    return "utf8"
                raise KeyError("Mock KeyError")

        # Mock the MYSQL_CHARACTER_SETS list with an entry that will cause a KeyError
        mock_character_sets = [
            None,  # Index 0
            MockTuple(),  # Index 1 - This will cause a KeyError when accessing index 1
        ]

        # Test with a specific charset
        with patch("sqlite3_to_mysql.mysql_utils.MYSQL_CHARACTER_SETS", mock_character_sets):
            result = list(mysql_supported_character_sets(charset="utf8"))
            # The function should skip the KeyError and return an empty list
            assert len(result) == 0

        # Test without a specific charset
        mock_get_supported = MagicMock(return_value=["utf8"])
        with patch("sqlite3_to_mysql.mysql_utils.MYSQL_CHARACTER_SETS", mock_character_sets):
            with patch("mysql.connector.CharacterSet.get_supported", mock_get_supported):
                result = list(mysql_supported_character_sets())
                # The function should skip the KeyError and return an empty list
                assert len(result) == 0

    def test_mysql_supported_character_sets_with_keyerror_in_charset_match(self) -> None:
        """Test mysql_supported_character_sets function with KeyError when matching charset."""

        # Create a mock tuple that will raise KeyError when checking if info[0] == charset
        class MockTuple:
            def __getitem__(self, key):
                if key == 0:
                    raise KeyError("Mock KeyError in charset match")
                if key == 1:
                    return "utf8_general_ci"
                return None

        # Mock the MYSQL_CHARACTER_SETS list with an entry that will cause a KeyError
        mock_character_sets = [
            None,  # Index 0
            MockTuple(),  # Index 1 - This will cause a KeyError when accessing info[0]
        ]

        # Test with a specific charset
        with patch("sqlite3_to_mysql.mysql_utils.MYSQL_CHARACTER_SETS", mock_character_sets):
            result = list(mysql_supported_character_sets(charset="utf8"))
            # The function should skip the KeyError and return an empty list
            assert len(result) == 0

    # -----------------------------
    # Expression defaults (MySQL 8.0.13+, MariaDB 10.2.0+)
    # -----------------------------
    @pytest.mark.parametrize(
        "ver, expected",
        [
            ("8.0.12", False),
            ("8.0.13", True),
            ("8.0.13-8ubuntu1", True),
            ("5.7.44", False),
        ],
    )
    def test_expr_defaults_mysql(self, ver: str, expected: bool) -> None:
        assert check_mysql_expression_defaults_support(ver) is expected

    @pytest.mark.parametrize(
        "ver, expected",
        [
            ("10.1.99-MariaDB", False),
            ("10.2.0-MariaDB", True),
            ("10.2.7-MariaDB-1~deb10u1", True),
            ("10.1.2-mArIaDb", False),  # case-insensitive detection
        ],
    )
    def test_expr_defaults_mariadb(self, ver: str, expected: bool) -> None:
        assert check_mysql_expression_defaults_support(ver) is expected

    # -----------------------------
    # CURRENT_TIMESTAMP for DATETIME (MySQL 5.6.5+, MariaDB 10.0.1+)
    # -----------------------------
    @pytest.mark.parametrize(
        "ver, expected",
        [
            ("5.6.4", False),
            ("5.6.5", True),
            ("5.6.5-ps-log", True),
            ("5.5.62", False),
        ],
    )
    def test_current_timestamp_datetime_mysql(self, ver: str, expected: bool) -> None:
        assert check_mysql_current_timestamp_datetime_support(ver) is expected

    @pytest.mark.parametrize(
        "ver, expected",
        [
            ("10.0.0-MariaDB", False),
            ("10.0.1-MariaDB", True),
            ("10.3.39-MariaDB-1:10.3.39+maria~focal", True),
        ],
    )
    def test_current_timestamp_datetime_mariadb(self, ver: str, expected: bool) -> None:
        assert check_mysql_current_timestamp_datetime_support(ver) is expected

    # -----------------------------
    # Fractional seconds (fsp) (MySQL 5.6.4+, MariaDB 10.1.2+)
    # -----------------------------
    @pytest.mark.parametrize(
        "ver, expected",
        [
            ("5.6.3", False),
            ("5.6.4", True),
            ("5.7.44-0ubuntu0.18.04.1", True),
        ],
    )
    def test_fractional_seconds_mysql(self, ver: str, expected: bool) -> None:
        assert check_mysql_fractional_seconds_support(ver) is expected

    @pytest.mark.parametrize(
        "ver, expected",
        [
            ("10.1.1-MariaDB", False),
            ("10.1.2-MariaDB", True),
            ("10.6.16-MariaDB-1:10.6.16+maria~jammy", True),
            ("10.1.2-mArIaDb", True),  # case-insensitive detection
        ],
    )
    def test_fractional_seconds_mariadb(self, ver: str, expected: bool) -> None:
        assert check_mysql_fractional_seconds_support(ver) is expected
