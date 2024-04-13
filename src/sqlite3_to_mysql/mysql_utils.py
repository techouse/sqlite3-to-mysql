"""MySQL helpers."""

import re
import typing as t

from mysql.connector import CharacterSet
from mysql.connector.charsets import MYSQL_CHARACTER_SETS
from packaging import version
from packaging.version import Version


# Shamelessly copied from SQLAlchemy's dialects/mysql/__init__.py
MYSQL_COLUMN_TYPES: t.Tuple[str, ...] = (
    "BIGINT",
    "BINARY",
    "BIT",
    "BLOB",
    "BOOLEAN",
    "CHAR",
    "DATE",
    "DATETIME",
    "DECIMAL",
    "DOUBLE",
    "ENUM",
    "FLOAT",
    "INTEGER",
    "JSON",
    "LONGBLOB",
    "LONGTEXT",
    "MEDIUMBLOB",
    "MEDIUMINT",
    "MEDIUMTEXT",
    "NCHAR",
    "NVARCHAR",
    "NUMERIC",
    "SET",
    "SMALLINT",
    "REAL",
    "TEXT",
    "TIME",
    "TIMESTAMP",
    "TINYBLOB",
    "TINYINT",
    "TINYTEXT",
    "VARBINARY",
    "VARCHAR",
    "YEAR",
)

MYSQL_TEXT_COLUMN_TYPES: t.Tuple[str, ...] = (
    "LONGTEXT",
    "MEDIUMTEXT",
    "TEXT",
    "TINYTEXT",
)

MYSQL_TEXT_COLUMN_TYPES_WITH_JSON: t.Tuple[str, ...] = ("JSON",) + MYSQL_TEXT_COLUMN_TYPES

MYSQL_BLOB_COLUMN_TYPES: t.Tuple[str, ...] = (
    "LONGBLOB",
    "MEDIUMBLOB",
    "BLOB",
    "TINYBLOB",
)

MYSQL_COLUMN_TYPES_WITHOUT_DEFAULT: t.Tuple[str, ...] = (
    ("GEOMETRY",) + MYSQL_TEXT_COLUMN_TYPES_WITH_JSON + MYSQL_BLOB_COLUMN_TYPES
)


MYSQL_INSERT_METHOD: t.Tuple[str, ...] = (
    "DEFAULT",
    "IGNORE",
    "UPDATE",
)


class CharSet(t.NamedTuple):
    """MySQL character set as a named tuple."""

    id: int
    charset: str
    collation: str


def mysql_supported_character_sets(charset: t.Optional[str] = None) -> t.Iterator[CharSet]:
    """Get supported MySQL character sets."""
    index: int
    info: t.Optional[t.Tuple[str, str, bool]]
    if charset is not None:
        for index, info in enumerate(MYSQL_CHARACTER_SETS):
            if info is not None:
                try:
                    if info[0] == charset:
                        yield CharSet(index, charset, info[1])
                except KeyError:
                    continue
    else:
        for charset in CharacterSet().get_supported():
            for index, info in enumerate(MYSQL_CHARACTER_SETS):
                if info is not None:
                    try:
                        yield CharSet(index, charset, info[1])
                    except KeyError:
                        continue


def get_mysql_version(version_string: str) -> version.Version:
    """Get MySQL version."""
    return version.parse(re.sub("-.*$", "", version_string))


def check_mysql_json_support(version_string: str) -> bool:
    """Check for MySQL JSON support."""
    mysql_version: Version = get_mysql_version(version_string)
    if version_string.lower().endswith("-mariadb"):
        if mysql_version.major >= 10 and mysql_version.minor >= 2 and mysql_version.micro >= 7:
            return True
    else:
        if mysql_version.major >= 8:
            return True
        if mysql_version.minor >= 7 and mysql_version.micro >= 8:
            return True
    return False


def check_mysql_fulltext_support(version_string: str) -> bool:
    """Check for FULLTEXT indexing support."""
    mysql_version: Version = get_mysql_version(version_string)
    if version_string.lower().endswith("-mariadb"):
        if mysql_version.major >= 10 and mysql_version.minor >= 0 and mysql_version.micro >= 5:
            return True
    else:
        if mysql_version.major >= 8:
            return True
        if mysql_version.minor >= 6:
            return True
    return False


def safe_identifier_length(identifier_name: str, max_length: int = 64) -> str:
    """https://dev.mysql.com/doc/refman/8.0/en/identifier-length.html."""
    return str(identifier_name)[:max_length]
