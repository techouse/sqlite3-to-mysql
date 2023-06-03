"""Types for sqlite3-to-mysql."""

import typing as t
from logging import Logger
from sqlite3 import Connection, Cursor

import typing_extensions as tx
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor


if t.TYPE_CHECKING:
    from _typeshed import FileDescriptorOrPath


class SQLite3toMySQLParams(tx.TypedDict):
    """SQLite3toMySQL parameters."""

    if t.TYPE_CHECKING:
        sqlite_file: t.Optional[FileDescriptorOrPath]
    else:
        sqlite_file: t.Any

    sqlite_tables: t.Optional[t.List[str]]
    without_foreign_keys: bool
    mysql_user: str
    mysql_password: t.Optional[str]
    mysql_host: t.Optional[str]
    mysql_port: t.Optional[int]
    mysql_ssl_disabled: bool
    chunk: t.Optional[int]
    quiet: bool
    log_file: t.Optional[str]
    mysql_database: t.Optional[str]
    mysql_integer_type: t.Optional[str]


class SQLite3toMySQLAttributes:
    """SQLite3toMySQL attributes."""

    _sqlite_file: t.AnyStr
    _sqlite_tables: t.Tuple[str, ...]
    _without_foreign_keys: bool
    _mysql_user: str
    _mysql_password: t.Optional[str]
    _mysql_host: str
    _mysql_port: int
    _mysql_ssl_disabled: bool
    _chunk_size: t.Optional[int]
    _quiet: bool
    _logger: Logger
    _log_file: str
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
    _sqlite: t.Optional[Connection]
    _sqlite_cur: t.Optional[Cursor]
    _sqlite_version: str
    _sqlite_table_xinfo_support: bool
    _mysql: t.Optional[MySQLConnection]
    _mysql_cur: t.Optional[MySQLCursor]
    _mysql_version: str
    _mysql_json_support: bool
    _mysql_fulltext_support: bool
