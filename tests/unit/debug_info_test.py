import platform
import sqlite3
import sys
from unittest.mock import MagicMock, patch

import pytest

from sqlite3_to_mysql.debug_info import _implementation, _mysql_version, info


class TestDebugInfo:
    def test_implementation_cpython(self) -> None:
        """Test _implementation function with CPython."""
        with patch("platform.python_implementation", return_value="CPython"):
            with patch("platform.python_version", return_value="3.8.0"):
                assert _implementation() == "CPython 3.8.0"

    def test_implementation_pypy(self) -> None:
        """Test _implementation function with PyPy."""
        with patch("platform.python_implementation", return_value="PyPy"):
            # Mock sys.pypy_version_info
            mock_version_info = MagicMock()
            mock_version_info.major = 7
            mock_version_info.minor = 3
            mock_version_info.micro = 1
            mock_version_info.releaselevel = "final"

            with patch.object(sys, "pypy_version_info", mock_version_info, create=True):
                assert _implementation() == "PyPy 7.3.1"

    def test_implementation_pypy_non_final(self) -> None:
        """Test _implementation function with PyPy non-final release."""
        with patch("platform.python_implementation", return_value="PyPy"):
            # Mock sys.pypy_version_info
            mock_version_info = MagicMock()
            mock_version_info.major = 7
            mock_version_info.minor = 3
            mock_version_info.micro = 1
            mock_version_info.releaselevel = "beta"

            with patch.object(sys, "pypy_version_info", mock_version_info, create=True):
                assert _implementation() == "PyPy 7.3.1beta"

    def test_implementation_jython(self) -> None:
        """Test _implementation function with Jython."""
        with patch("platform.python_implementation", return_value="Jython"):
            with patch("platform.python_version", return_value="2.7.2"):
                assert _implementation() == "Jython 2.7.2"

    def test_implementation_ironpython(self) -> None:
        """Test _implementation function with IronPython."""
        with patch("platform.python_implementation", return_value="IronPython"):
            with patch("platform.python_version", return_value="2.7.9"):
                assert _implementation() == "IronPython 2.7.9"

    def test_implementation_unknown(self) -> None:
        """Test _implementation function with unknown implementation."""
        with patch("platform.python_implementation", return_value="Unknown"):
            assert _implementation() == "Unknown Unknown"

    def test_mysql_version_found(self) -> None:
        """Test _mysql_version function when MySQL is found."""
        with patch("sqlite3_to_mysql.debug_info.which", return_value="/usr/bin/mysql"):
            with patch("sqlite3_to_mysql.debug_info.check_output", return_value=b"mysql  Ver 8.0.23"):
                assert _mysql_version() == "mysql  Ver 8.0.23"

    def test_mysql_version_decode_error(self) -> None:
        """Test _mysql_version function with decode error."""
        with patch("sqlite3_to_mysql.debug_info.which", return_value="/usr/bin/mysql"):
            with patch("sqlite3_to_mysql.debug_info.check_output", return_value=b"\xff\xfe"):
                # This should trigger a UnicodeDecodeError
                result = _mysql_version()
                assert "b'" in result  # Should contain the string representation of bytes

    def test_mysql_version_exception(self) -> None:
        """Test _mysql_version function with exception."""
        with patch("sqlite3_to_mysql.debug_info.which", return_value="/usr/bin/mysql"):
            with patch("sqlite3_to_mysql.debug_info.check_output", side_effect=Exception("Command failed")):
                assert _mysql_version() == "MySQL client not found on the system"

    def test_mysql_version_not_found(self) -> None:
        """Test _mysql_version function when MySQL is not found."""
        with patch("sqlite3_to_mysql.debug_info.which", return_value=None):
            assert _mysql_version() == "MySQL client not found on the system"

    def test_info(self) -> None:
        """Test info function."""
        with patch("platform.system", return_value="Linux"):
            with patch("platform.release", return_value="5.4.0"):
                with patch("sqlite3_to_mysql.debug_info._implementation", return_value="CPython 3.8.0"):
                    with patch("sqlite3_to_mysql.debug_info._mysql_version", return_value="mysql  Ver 8.0.23"):
                        with patch.object(sqlite3, "sqlite_version", "3.32.3"):
                            result = info()
                            assert result[0][0] == "sqlite3-to-mysql"
                            assert result[2][0] == "Operating System"
                            assert result[2][1] == "Linux 5.4.0"
                            assert result[3][0] == "Python"
                            assert result[3][1] == "CPython 3.8.0"
                            assert result[4][0] == "MySQL"
                            assert result[4][1] == "mysql  Ver 8.0.23"
                            assert result[5][0] == "SQLite"
                            assert result[5][1] == "3.32.3"

    def test_info_platform_error(self) -> None:
        """Test info function with platform error."""
        with patch("platform.system", side_effect=IOError("Platform error")):
            with patch("sqlite3_to_mysql.debug_info._implementation", return_value="CPython 3.8.0"):
                with patch("sqlite3_to_mysql.debug_info._mysql_version", return_value="mysql  Ver 8.0.23"):
                    with patch.object(sqlite3, "sqlite_version", "3.32.3"):
                        result = info()
                        assert result[0][0] == "sqlite3-to-mysql"
                        assert result[2][0] == "Operating System"
                        assert result[2][1] == "Unknown"
                        assert result[3][0] == "Python"
                        assert result[3][1] == "CPython 3.8.0"
                        assert result[4][0] == "MySQL"
                        assert result[4][1] == "mysql  Ver 8.0.23"
                        assert result[5][0] == "SQLite"
                        assert result[5][1] == "3.32.3"
