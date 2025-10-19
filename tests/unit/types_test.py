import os
import typing as t
from logging import Logger
from sqlite3 import Connection, Cursor
from unittest.mock import MagicMock

import pytest
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor

from sqlite3_to_mysql.types import SQLite3toMySQLAttributes, SQLite3toMySQLParams


class TestTypes:
    def test_sqlite3_to_mysql_params_typing(self) -> None:
        """Test SQLite3toMySQLParams typing."""
        # Create a valid params dict
        params: SQLite3toMySQLParams = {
            "sqlite_file": "test.db",
            "sqlite_tables": ["table1", "table2"],
            "exclude_sqlite_tables": ["skip_this"],
            "sqlite_views_as_tables": False,
            "without_foreign_keys": False,
            "mysql_user": "user",
            "mysql_password": "password",
            "mysql_host": "localhost",
            "mysql_port": 3306,
            "mysql_socket": "/var/run/mysqld/mysqld.sock",
            "mysql_ssl_disabled": True,
            "chunk": 1000,
            "quiet": False,
            "log_file": "log.txt",
            "mysql_database": "test_db",
            "mysql_integer_type": "INT",
            "mysql_create_tables": True,
            "mysql_truncate_tables": False,
            "mysql_transfer_data": True,
            "mysql_charset": "utf8mb4",
            "mysql_collation": "utf8mb4_unicode_ci",
            "ignore_duplicate_keys": False,
            "use_fulltext": True,
            "with_rowid": False,
            "mysql_insert_method": "INSERT",
            "mysql_string_type": "VARCHAR",
            "mysql_text_type": "TEXT",
        }

        # Test that all fields are accessible
        assert params["sqlite_file"] == "test.db"
        assert params["sqlite_tables"] == ["table1", "table2"]
        assert params["exclude_sqlite_tables"] == ["skip_this"]
        assert params["sqlite_views_as_tables"] is False
        assert params["without_foreign_keys"] is False
        assert params["mysql_user"] == "user"
        assert params["mysql_password"] == "password"
        assert params["mysql_host"] == "localhost"
        assert params["mysql_port"] == 3306
        assert params["mysql_socket"] == "/var/run/mysqld/mysqld.sock"
        assert params["mysql_ssl_disabled"] is True
        assert params["chunk"] == 1000
        assert params["quiet"] is False
        assert params["log_file"] == "log.txt"
        assert params["mysql_database"] == "test_db"
        assert params["mysql_integer_type"] == "INT"
        assert params["mysql_create_tables"] is True
        assert params["mysql_truncate_tables"] is False
        assert params["mysql_transfer_data"] is True
        assert params["mysql_charset"] == "utf8mb4"
        assert params["mysql_collation"] == "utf8mb4_unicode_ci"
        assert params["ignore_duplicate_keys"] is False
        assert params["use_fulltext"] is True
        assert params["with_rowid"] is False
        assert params["mysql_insert_method"] == "INSERT"
        assert params["mysql_string_type"] == "VARCHAR"
        assert params["mysql_text_type"] == "TEXT"

        # Test with optional fields omitted
        minimal_params: SQLite3toMySQLParams = {"sqlite_file": "test.db"}
        assert minimal_params["sqlite_file"] == "test.db"

        # Test with PathLike object
        path_like_params: SQLite3toMySQLParams = {"sqlite_file": os.path.join("path", "to", "test.db")}
        assert path_like_params["sqlite_file"] == os.path.join("path", "to", "test.db")

    def test_sqlite3_to_mysql_attributes_typing(self) -> None:
        """Test SQLite3toMySQLAttributes typing."""

        # Create a mock class that inherits from SQLite3toMySQLAttributes
        class MockSQLite3toMySQL(SQLite3toMySQLAttributes):
            def __init__(self) -> None:
                # Initialize all required attributes
                self._sqlite_file = "test.db"
                self._sqlite_tables = ["table1", "table2"]
                self._exclude_sqlite_tables = []
                self._sqlite_views_as_tables = False
                self._without_foreign_keys = False
                self._mysql_user = "user"
                self._mysql_password = "password"
                self._mysql_host = "localhost"
                self._mysql_port = 3306
                self._mysql_socket = "/var/run/mysqld/mysqld.sock"
                self._mysql_ssl_disabled = True
                self._chunk_size = 1000
                self._quiet = False
                self._logger = MagicMock(spec=Logger)
                self._log_file = "log.txt"
                self._mysql_database = "test_db"
                self._mysql_insert_method = "INSERT"
                self._mysql_create_tables = True
                self._mysql_truncate_tables = False
                self._mysql_transfer_data = True
                self._mysql_integer_type = "INT"
                self._mysql_string_type = "VARCHAR"
                self._mysql_text_type = "TEXT"
                self._mysql_charset = "utf8mb4"
                self._mysql_collation = "utf8mb4_unicode_ci"
                self._ignore_duplicate_keys = False
                self._use_fulltext = True
                self._with_rowid = False
                self._sqlite = MagicMock(spec=Connection)
                self._sqlite_cur = MagicMock(spec=Cursor)
                self._sqlite_version = "3.32.3"
                self._sqlite_table_xinfo_support = True
                self._mysql = MagicMock(spec=MySQLConnection)
                self._mysql_cur = MagicMock(spec=MySQLCursor)
                self._mysql_version = "8.0.23"
                self._mysql_json_support = True
                self._mysql_fulltext_support = True

        # Create an instance of the mock class
        instance = MockSQLite3toMySQL()

        # Test that all attributes are accessible
        assert instance._sqlite_file == "test.db"
        assert instance._sqlite_tables == ["table1", "table2"]
        assert instance._exclude_sqlite_tables == []
        assert instance._sqlite_views_as_tables is False
        assert instance._without_foreign_keys is False
        assert instance._mysql_user == "user"
        assert instance._mysql_password == "password"
        assert instance._mysql_host == "localhost"
        assert instance._mysql_port == 3306
        assert instance._mysql_socket == "/var/run/mysqld/mysqld.sock"
        assert instance._mysql_ssl_disabled is True
        assert instance._chunk_size == 1000
        assert instance._quiet is False
        assert instance._log_file == "log.txt"
        assert instance._mysql_database == "test_db"
        assert instance._mysql_insert_method == "INSERT"
        assert instance._mysql_create_tables is True
        assert instance._mysql_truncate_tables is False
        assert instance._mysql_transfer_data is True
        assert instance._mysql_integer_type == "INT"
        assert instance._mysql_string_type == "VARCHAR"
        assert instance._mysql_text_type == "TEXT"
        assert instance._mysql_charset == "utf8mb4"
        assert instance._mysql_collation == "utf8mb4_unicode_ci"
        assert instance._ignore_duplicate_keys is False
        assert instance._use_fulltext is True
        assert instance._with_rowid is False
        assert instance._sqlite_version == "3.32.3"
        assert instance._sqlite_table_xinfo_support is True
        assert instance._mysql_version == "8.0.23"
        assert instance._mysql_json_support is True
        assert instance._mysql_fulltext_support is True
