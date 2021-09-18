"""MySQL helpers."""
import re
from collections import namedtuple

from packaging import version
from mysql.connector import CharacterSet
from mysql.connector.charsets import MYSQL_CHARACTER_SETS

# Shamelessly copied from SQLAlchemy's dialects/mysql/__init__.py
MYSQL_COLUMN_TYPES = {
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
    "DECIMAL",
    "FLOAT",
    "INTEGER",
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
}

CharSet = namedtuple("CharSet", ["id", "charset", "collation"])


def mysql_supported_character_sets(charset=None):
    """Get supported MySQL character sets."""
    if charset is not None:
        for index, info in enumerate(MYSQL_CHARACTER_SETS):
            if info is not None:
                try:
                    if info[0] == charset:
                        yield CharSet(index, charset, info[1])
                except KeyError:
                    continue
    else:
        for charset in CharacterSet.get_supported():
            for index, info in enumerate(MYSQL_CHARACTER_SETS):
                if info is not None:
                    try:
                        yield CharSet(index, charset, info[1])
                    except KeyError:
                        continue


def get_mysql_version(version_string):
    """Get MySQL version."""
    return version.parse(re.sub("-.*$", "", version_string))


def check_mysql_json_support(version_string):
    """Check for MySQL JSON support."""
    mysql_version = get_mysql_version(version_string)
    if version_string.lower().endswith("-mariadb"):
        if (
            mysql_version.major >= 10
            and mysql_version.minor >= 2
            and mysql_version.micro >= 7
        ):
            return True
    else:
        if mysql_version.major >= 8:
            return True
        if mysql_version.minor >= 7 and mysql_version.micro >= 8:
            return True
    return False


def check_mysql_fulltext_support(version_string):
    """Check for FULLTEXT indexing support."""
    mysql_version = get_mysql_version(version_string)
    if version_string.lower().endswith("-mariadb"):
        if (
            mysql_version.major >= 10
            and mysql_version.minor >= 0
            and mysql_version.micro >= 5
        ):
            return True
    else:
        if mysql_version.major >= 8:
            return True
        if mysql_version.minor >= 6:
            return True
    return False


def safe_identifier_length(identifier_name, max_length=64):
    """https://dev.mysql.com/doc/refman/8.0/en/identifier-length.html."""
    return identifier_name[:max_length]
