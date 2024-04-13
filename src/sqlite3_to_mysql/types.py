"""Types for sqlite3-to-mysql."""

import os
import typing as t
from logging import Logger
from sqlite3 import Connection, Cursor

import typing_extensions as tx
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor


class SQLite3toMySQLParams(tx.TypedDict):
    """SQLite3toMySQL parameters."""

    sqlite_file: t.Union[str, "os.PathLike[t.Any]"]
    sqlite_tables: t.Optional[t.Sequence[str]]
    without_foreign_keys: t.Optional[bool]
    mysql_user: t.Optional[str]
    mysql_password: t.Optional[t.Union[str, bool]]
    mysql_host: t.Optional[str]
    mysql_port: t.Optional[int]
    mysql_ssl_disabled: t.Optional[bool]
    chunk: t.Optional[int]
    quiet: t.Optional[bool]
    log_file: t.Optional[t.Union[str, "os.PathLike[t.Any]"]]
    mysql_database: t.Optional[str]
    mysql_integer_type: t.Optional[str]
    mysql_truncate_tables: t.Optional[bool]
    mysql_charset: t.Optional[str]
    mysql_collation: t.Optional[str]
    ignore_duplicate_keys: t.Optional[bool]
    use_fulltext: t.Optional[bool]
    with_rowid: t.Optional[bool]
    mysql_insert_method: t.Optional[str]
    mysql_string_type: t.Optional[str]
    mysql_text_type: t.Optional[str]


class SQLite3toMySQLAttributes:
    """SQLite3toMySQL attributes."""

    _sqlite_file: t.Union[str, "os.PathLike[t.Any]"]
    _sqlite_tables: t.Sequence[str]
    _without_foreign_keys: bool
    _mysql_user: str
    _mysql_password: t.Optional[str]
    _mysql_host: str
    _mysql_port: int
    _mysql_ssl_disabled: bool
    _chunk_size: t.Optional[int]
    _quiet: bool
    _logger: Logger
    _log_file: t.Union[str, "os.PathLike[t.Any]"]
    _mysql_database: str
    _mysql_insert_method: str
    _mysql_truncate_tables: bool
    _mysql_integer_type: str
    _mysql_string_type: str
    _mysql_text_type: str
    _mysql_charset: str
    _mysql_collation: str
    _ignore_duplicate_keys: bool
    _use_fulltext: bool
    _with_rowid: bool
    _sqlite: Connection
    _sqlite_cur: Cursor
    _sqlite_version: str
    _sqlite_table_xinfo_support: bool
    _mysql: MySQLConnection
    _mysql_cur: MySQLCursor
    _mysql_version: str
    _mysql_json_support: bool
    _mysql_fulltext_support: bool
