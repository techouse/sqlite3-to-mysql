"""Use to transfer an SQLite 3 database to MySQL."""

import logging
import os
import re
import sqlite3
import typing as t
from datetime import timedelta
from decimal import Decimal
from itertools import chain
from math import ceil
from os.path import isfile, realpath
from sys import stdout

import mysql.connector
import sqlglot
from mysql.connector import CharacterSet
from mysql.connector import __version__ as mysql_connector_version_string
from mysql.connector import errorcode
from packaging import version
from sqlglot import errors as sqlglot_errors
from sqlglot import expressions as exp
from sqlglot.dialects import mysql as sqlglot_mysql
from sqlglot.time import format_time as sqlglot_format_time
from sqlglot.trie import new_trie
from tqdm import tqdm, trange


try:
    # Python 3.11+
    from typing import Unpack  # type: ignore[attr-defined]
except ImportError:
    # Python < 3.11
    from typing_extensions import Unpack  # type: ignore

from sqlite3_to_mysql.sqlite_utils import (
    adapt_decimal,
    adapt_timedelta,
    check_sqlite_table_xinfo_support,
    convert_date,
    convert_decimal,
    convert_timedelta,
    unicase_compare,
)

from .mysql_utils import (
    MYSQL_BLOB_COLUMN_TYPES,
    MYSQL_COLUMN_TYPES,
    MYSQL_INSERT_METHOD,
    MYSQL_TEXT_COLUMN_TYPES,
    MYSQL_TEXT_COLUMN_TYPES_WITH_JSON,
    check_mysql_current_timestamp_datetime_support,
    check_mysql_expression_defaults_support,
    check_mysql_fractional_seconds_support,
    check_mysql_fulltext_support,
    check_mysql_json_support,
    check_mysql_values_alias_support,
    safe_identifier_length,
)
from .types import SQLite3toMySQLAttributes, SQLite3toMySQLParams


SQLGLOT_MYSQL_INVERSE_TIME_MAPPING: t.Dict[str, str] = {
    key: value for key, value in sqlglot_mysql.MySQL.INVERSE_TIME_MAPPING.items() if key != "%H:%M:%S"
}
SQLGLOT_MYSQL_INVERSE_TIME_TRIE: t.Dict[str, t.Any] = new_trie(SQLGLOT_MYSQL_INVERSE_TIME_MAPPING)


class SQLite3toMySQL(SQLite3toMySQLAttributes):
    """Use this class to transfer an SQLite 3 database to MySQL."""

    COLUMN_PATTERN: t.Pattern[str] = re.compile(r"^[^(]+")
    COLUMN_LENGTH_PATTERN: t.Pattern[str] = re.compile(r"\(\d+\)")
    COLUMN_PRECISION_AND_SCALE_PATTERN: t.Pattern[str] = re.compile(r"\(\d+,\d+\)")
    COLUMN_UNSIGNED_PATTERN: t.Pattern[str] = re.compile(r"\bUNSIGNED\b", re.IGNORECASE)
    CURRENT_TS: t.Pattern[str] = re.compile(r"^CURRENT_TIMESTAMP(?:\s*\(\s*\))?$", re.IGNORECASE)
    CURRENT_DATE: t.Pattern[str] = re.compile(r"^CURRENT_DATE(?:\s*\(\s*\))?$", re.IGNORECASE)
    CURRENT_TIME: t.Pattern[str] = re.compile(r"^CURRENT_TIME(?:\s*\(\s*\))?$", re.IGNORECASE)
    SQLITE_NOW_FUNC: t.Pattern[str] = re.compile(
        r"^(datetime|date|time)\s*\(\s*'now'(?:\s*,\s*'(localtime|utc)')?\s*\)$",
        re.IGNORECASE,
    )
    STRFTIME_NOW: t.Pattern[str] = re.compile(
        r"^strftime\s*\(\s*'([^']+)'\s*,\s*'now'(?:\s*,\s*'(localtime|utc)')?\s*\)$",
        re.IGNORECASE,
    )
    NUMERIC_LITERAL_PATTERN: t.Pattern[str] = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")

    MYSQL_CONNECTOR_VERSION: version.Version = version.parse(mysql_connector_version_string)

    def __init__(self, **kwargs: Unpack[SQLite3toMySQLParams]):
        """Constructor."""
        if kwargs.get("sqlite_file") is None:
            raise ValueError("Please provide an SQLite file")
        elif not isfile(str(kwargs.get("sqlite_file"))):
            raise FileNotFoundError("SQLite file does not exist")
        else:
            self._sqlite_file = realpath(str(kwargs.get("sqlite_file")))

        if kwargs.get("mysql_user") is not None:
            self._mysql_user = str(kwargs.get("mysql_user"))
        else:
            raise ValueError("Please provide a MySQL user")

        self._mysql_password = str(kwargs.get("mysql_password")) if kwargs.get("mysql_password") else None

        self._mysql_host = str(kwargs.get("mysql_host", "localhost"))

        self._mysql_port = kwargs.get("mysql_port", 3306) or 3306

        self._is_mariadb = False

        if kwargs.get("mysql_socket") is not None:
            if not os.path.exists(str(kwargs.get("mysql_socket"))):
                raise FileNotFoundError("MySQL socket does not exist")
            else:
                self._mysql_socket = realpath(str(kwargs.get("mysql_socket")))
                self._mysql_host = None
                self._mysql_port = None
        else:
            self._mysql_socket = None

        self._sqlite_tables = kwargs.get("sqlite_tables") or tuple()

        self._exclude_sqlite_tables = kwargs.get("exclude_sqlite_tables") or tuple()

        self._sqlite_views_as_tables = bool(kwargs.get("sqlite_views_as_tables", False))

        if bool(self._sqlite_tables) and bool(self._exclude_sqlite_tables):
            raise ValueError("Please provide either sqlite_tables or exclude_sqlite_tables, not both")

        if bool(self._sqlite_tables) or bool(self._exclude_sqlite_tables):
            self._without_foreign_keys = True
        else:
            self._without_foreign_keys = bool(kwargs.get("without_foreign_keys", False))

        self._mysql_ssl_disabled = bool(kwargs.get("mysql_ssl_disabled", False))

        # Expect an integer chunk size; normalize to None when unset/invalid or <= 0
        _chunk = kwargs.get("chunk")
        self._chunk_size = _chunk if isinstance(_chunk, int) and _chunk > 0 else None

        self._quiet = bool(kwargs.get("quiet", False))

        self._logger = self._setup_logger(log_file=kwargs.get("log_file", None), quiet=self._quiet)

        self._mysql_database = kwargs.get("mysql_database", "transfer") or "transfer"

        self._mysql_insert_method = str(kwargs.get("mysql_insert_method", "IGNORE")).upper()
        if self._mysql_insert_method not in MYSQL_INSERT_METHOD:
            self._mysql_insert_method = "IGNORE"

        self._mysql_truncate_tables = bool(kwargs.get("mysql_truncate_tables", False))

        self._mysql_integer_type = str(kwargs.get("mysql_integer_type", "INT(11)")).upper()

        self._mysql_string_type = str(kwargs.get("mysql_string_type", "VARCHAR(255)")).upper()

        self._mysql_text_type = str(kwargs.get("mysql_text_type", "TEXT")).upper()
        if self._mysql_text_type not in MYSQL_TEXT_COLUMN_TYPES:
            self._mysql_text_type = "TEXT"

        self._mysql_charset = kwargs.get("mysql_charset", "utf8mb4") or "utf8mb4"

        self._mysql_collation = (
            kwargs.get("mysql_collation") or CharacterSet().get_default_collation(self._mysql_charset.lower())[0]
        )
        if not kwargs.get("mysql_collation") and self._mysql_collation == "utf8mb4_0900_ai_ci":
            self._mysql_collation = "utf8mb4_unicode_ci"

        self._ignore_duplicate_keys = kwargs.get("ignore_duplicate_keys", False) or False

        self._use_fulltext = kwargs.get("use_fulltext", False) or False

        self._with_rowid = kwargs.get("with_rowid", False) or False

        sqlite3.register_adapter(Decimal, adapt_decimal)
        sqlite3.register_converter("DECIMAL", convert_decimal)
        sqlite3.register_adapter(timedelta, adapt_timedelta)
        sqlite3.register_converter("DATE", convert_date)
        sqlite3.register_converter("TIME", convert_timedelta)

        self._sqlite = sqlite3.connect(realpath(self._sqlite_file), detect_types=sqlite3.PARSE_DECLTYPES)
        self._sqlite.row_factory = sqlite3.Row
        self._sqlite.create_collation("unicase", unicase_compare)

        self._sqlite_cur = self._sqlite.cursor()

        self._sqlite_version = self._get_sqlite_version()
        self._sqlite_table_xinfo_support = check_sqlite_table_xinfo_support(self._sqlite_version)

        self._mysql_create_tables = bool(kwargs.get("mysql_create_tables", True))
        self._mysql_transfer_data = bool(kwargs.get("mysql_transfer_data", True))

        if not self._mysql_transfer_data and not self._mysql_create_tables:
            raise ValueError("Unable to continue without transferring data or creating tables!")

        connection_args: t.Dict[str, t.Any] = {
            "user": self._mysql_user,
            "use_pure": True,
            "charset": self._mysql_charset,
            "collation": self._mysql_collation,
        }
        if self._mysql_password is not None:
            connection_args["password"] = self._mysql_password
        if self._mysql_socket is not None:
            connection_args["unix_socket"] = self._mysql_socket
        else:
            connection_args["host"] = self._mysql_host
            connection_args["port"] = self._mysql_port
            if self._mysql_ssl_disabled:
                connection_args["ssl_disabled"] = True

        try:
            _mysql_connection = mysql.connector.connect(**connection_args)
            if isinstance(_mysql_connection, mysql.connector.MySQLConnection):
                self._mysql = _mysql_connection
            else:
                raise ConnectionError("Unable to connect to MySQL")
            if not self._mysql.is_connected():
                raise ConnectionError("Unable to connect to MySQL")

            self._mysql_cur = self._mysql.cursor(prepared=True)

            try:
                self._mysql.database = self._mysql_database
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_BAD_DB_ERROR:
                    self._create_database()
                else:
                    self._logger.error(err)
                    raise

            self._mysql_version = self._get_mysql_version()
            self._is_mariadb = "-mariadb" in self._mysql_version.lower()
            self._mysql_json_support = check_mysql_json_support(self._mysql_version)
            self._mysql_fulltext_support = check_mysql_fulltext_support(self._mysql_version)
            self._allow_expr_defaults = check_mysql_expression_defaults_support(self._mysql_version)
            self._allow_current_ts_dt = check_mysql_current_timestamp_datetime_support(self._mysql_version)
            self._allow_fsp = check_mysql_fractional_seconds_support(self._mysql_version)

            if self._use_fulltext and not self._mysql_fulltext_support:
                raise ValueError("Your MySQL version does not support InnoDB FULLTEXT indexes!")
        except mysql.connector.Error as err:
            self._logger.error(err)
            raise

    @classmethod
    def _setup_logger(
        cls, log_file: t.Optional[t.Union[str, "os.PathLike[t.Any]"]] = None, quiet: bool = False
    ) -> logging.Logger:
        formatter = logging.Formatter(fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        logger = logging.getLogger(cls.__name__)
        logger.setLevel(logging.DEBUG)

        if not quiet:
            screen_handler = logging.StreamHandler(stream=stdout)
            screen_handler.setFormatter(formatter)
            logger.addHandler(screen_handler)

        if log_file:
            file_handler = logging.FileHandler(realpath(log_file), mode="w")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def _get_mysql_version(self) -> str:
        try:
            self._mysql_cur.execute("SHOW VARIABLES LIKE 'version'")
            row = self._mysql_cur.fetchone()
            if row:
                return str(row[1])
            else:
                self._logger.error("MySQL failed checking for InnoDB version")
                raise mysql.connector.Error("MySQL failed checking for InnoDB version")
        except (IndexError, mysql.connector.Error) as err:
            self._logger.error(
                "MySQL failed checking for InnoDB version: %s",
                err,
            )
            raise

    def _get_sqlite_version(self) -> str:
        try:
            self._sqlite_cur.execute("SELECT sqlite_version()")
            return str(self._sqlite_cur.fetchone()[0])
        except (IndexError, sqlite3.Error) as err:
            self._logger.error(
                "SQLite failed checking for InnoDB version: %s",
                err,
            )
            raise

    @staticmethod
    def _sqlite_quote_ident(name: str) -> str:
        """Return a SQLite identifier with internal quotes escaped."""
        return str(name).replace('"', '""')

    def _get_table_info(self, table_name: str) -> t.List[t.Dict[str, t.Any]]:
        """Fetch SQLite PRAGMA table information for a table."""
        quoted_table_name: str = self._sqlite_quote_ident(table_name)
        pragma: str = "table_xinfo" if self._sqlite_table_xinfo_support else "table_info"
        self._sqlite_cur.execute(f'PRAGMA {pragma}("{quoted_table_name}")')
        return [dict(row) for row in self._sqlite_cur.fetchall()]

    def _get_table_primary_key_columns(self, table_name: str) -> t.List[str]:
        """Return visible primary key columns ordered by their PK sequence."""
        primary_key_rows: t.List[t.Dict[str, t.Any]] = sorted(
            (
                column
                for column in self._get_table_info(table_name)
                if column.get("pk", 0) > 0 and column.get("hidden", 0) not in (1, 2, 3)
            ),
            key=lambda column: column.get("pk", 0),
        )
        return [safe_identifier_length(column["name"]) for column in primary_key_rows]

    def _sqlite_table_has_rowid(self, table: str) -> bool:
        try:
            quoted_table: str = self._sqlite_quote_ident(table)
            self._sqlite_cur.execute(f'SELECT rowid FROM "{quoted_table}" LIMIT 1')
            self._sqlite_cur.fetchall()
            return True
        except sqlite3.OperationalError:
            return False

    def _create_database(self) -> None:
        try:
            self._mysql_cur.execute(
                f"""
                CREATE DATABASE IF NOT EXISTS `{self._mysql_database}`
                DEFAULT CHARACTER SET {self._mysql_charset}
                DEFAULT COLLATE {self._mysql_collation}
            """
            )
            self._mysql_cur.close()
            self._mysql.commit()
            self._mysql.database = self._mysql_database
            self._mysql_cur = self._mysql.cursor(prepared=True)  # pylint: disable=W0201
        except mysql.connector.Error as err:
            self._logger.error(
                "MySQL failed creating databse %s: %s",
                self._mysql_database,
                err,
            )
            raise

    @classmethod
    def _valid_column_type(cls, column_type: str) -> t.Optional[t.Match[str]]:
        return cls.COLUMN_PATTERN.match(column_type.strip())

    @classmethod
    def _base_mysql_column_type(cls, column_type: str) -> str:
        stripped: str = column_type.strip()
        if not stripped:
            return ""
        match = cls._valid_column_type(stripped)
        if match:
            return match.group(0).strip().upper()
        return stripped.split("(", 1)[0].strip().upper()

    def _column_type_supports_default(self, base_type: str, allow_expr_defaults: bool) -> bool:
        normalized: str = base_type.upper()
        if not normalized:
            return True
        if normalized == "GEOMETRY":
            return False
        if normalized in MYSQL_BLOB_COLUMN_TYPES:
            return False
        if normalized in MYSQL_TEXT_COLUMN_TYPES_WITH_JSON:
            return allow_expr_defaults
        return True

    @staticmethod
    def _parse_sql_expression(value: str) -> t.Optional[exp.Expression]:
        stripped: str = value.strip()
        if not stripped:
            return None
        for dialect in ("mysql", "sqlite"):
            try:
                return sqlglot.parse_one(stripped, read=dialect)
            except sqlglot_errors.ParseError:
                continue
        return None

    def _format_textual_default(
        self,
        default_sql: str,
        allow_expr_defaults: bool,
        is_mariadb: bool,
    ) -> str:
        """Normalise textual DEFAULT expressions and wrap for MySQL via sqlglot."""
        stripped: str = default_sql.strip()
        if not stripped or stripped.upper() == "NULL":
            return stripped
        if not allow_expr_defaults:
            return stripped

        expr: t.Optional[exp.Expression] = self._parse_sql_expression(stripped)
        if expr is None:
            if is_mariadb or stripped.startswith("("):
                return stripped
            return f"({stripped})"

        formatted: str = expr.sql(dialect="mysql")
        if is_mariadb:
            return formatted

        if isinstance(expr, exp.Paren):
            return formatted

        wrapped = exp.Paren(this=expr.copy())
        return wrapped.sql(dialect="mysql")

    def _translate_type_from_sqlite_to_mysql(self, column_type: str) -> str:
        normalized: t.Optional[str] = self._normalize_sqlite_column_type(column_type)
        if normalized and normalized.upper() != column_type.upper():
            self._logger.info("Normalised SQLite column type %r -> %r", column_type, normalized)
            try:
                return self._translate_type_from_sqlite_to_mysql_legacy(normalized)
            except ValueError:
                pass
        return self._translate_type_from_sqlite_to_mysql_legacy(column_type)

    def _normalize_sqlite_column_type(self, column_type: str) -> t.Optional[str]:
        clean_type: str = column_type.strip()
        if not clean_type:
            return None

        normalized_for_parse: str = clean_type.upper().replace("UNSIGNED BIG INT", "BIGINT UNSIGNED")
        try:
            expression = sqlglot.parse_one(f"SELECT CAST(NULL AS {normalized_for_parse})", read="sqlite")
        except sqlglot_errors.ParseError:
            # Retry: strip UNSIGNED to aid parsing; we'll re-attach it below if present.
            try:
                no_unsigned = re.sub(r"\bUNSIGNED\b", "", normalized_for_parse).strip()
                expression = sqlglot.parse_one(f"SELECT CAST(NULL AS {no_unsigned})", read="sqlite")
            except sqlglot_errors.ParseError:
                return None

        cast: t.Optional[exp.Cast] = expression.find(exp.Cast)
        if not cast or not isinstance(cast.to, exp.DataType):
            return None

        params: t.List[str] = []
        for expr_param in cast.to.expressions or []:
            value_expr = expr_param.this if isinstance(expr_param, exp.DataTypeParam) else expr_param
            if value_expr is None:
                continue
            params.append(value_expr.sql(dialect="mysql"))

        base_match: t.Optional[t.Match[str]] = self._valid_column_type(clean_type)
        base = base_match.group(0).upper().strip() if base_match else clean_type.upper()

        normalized = base
        if params:
            normalized += "(" + ",".join(param.strip("\"'") for param in params) + ")"

        if "UNSIGNED" in clean_type.upper() and "UNSIGNED" not in normalized.upper().split():
            normalized = f"{normalized} UNSIGNED"

        return normalized

    def _translate_type_from_sqlite_to_mysql_legacy(self, column_type: str) -> str:
        """This could be optimized even further, however is seems adequate."""
        full_column_type: str = column_type.upper()
        unsigned: bool = self.COLUMN_UNSIGNED_PATTERN.search(full_column_type) is not None
        match: t.Optional[t.Match[str]] = self._valid_column_type(column_type)
        if not match:
            raise ValueError(f'"{column_type}" is not a valid column_type!')

        data_type: str = match.group(0).upper()

        if data_type in {"TEXT", "CLOB", "STRING"}:
            return self._mysql_text_type
        if data_type in {"CHARACTER", "NCHAR", "NATIVE CHARACTER"}:
            return "CHAR" + self._column_type_length(column_type)
        if data_type in {"VARYING CHARACTER", "NVARCHAR", "VARCHAR"}:
            if self._mysql_string_type in MYSQL_TEXT_COLUMN_TYPES:
                return self._mysql_string_type
            length = self._column_type_length(column_type)
            if not length:
                return self._mysql_string_type
            match = self._valid_column_type(self._mysql_string_type)
            if match:
                return match.group(0).upper() + length
        if data_type == "UNSIGNED BIG INT":
            return f"BIGINT{self._column_type_length(column_type)} UNSIGNED"
        if data_type.startswith(("TINYINT", "INT1")):
            return f"TINYINT{self._column_type_length(column_type)}{' UNSIGNED' if unsigned else ''}"
        if data_type.startswith(("SMALLINT", "INT2")):
            return f"SMALLINT{self._column_type_length(column_type)}{' UNSIGNED' if unsigned else ''}"
        if data_type.startswith(("MEDIUMINT", "INT3")):
            return f"MEDIUMINT{self._column_type_length(column_type)}{' UNSIGNED' if unsigned else ''}"
        if data_type.startswith("INT4"):
            return f"INT{self._column_type_length(column_type)}{' UNSIGNED' if unsigned else ''}"
        if data_type.startswith(("BIGINT", "INT8")):
            return f"BIGINT{self._column_type_length(column_type)}{' UNSIGNED' if unsigned else ''}"
        if data_type.startswith(("INT64", "NUMERIC")):
            if data_type == "NUMERIC" and self._column_type_precision_and_scale(full_column_type) != "":
                return f"DECIMAL{self._column_type_precision_and_scale(column_type)}{' UNSIGNED' if unsigned else ''}"
            return f"BIGINT{self._column_type_length(column_type, 19)}{' UNSIGNED' if unsigned else ''}"
        if data_type.startswith(("INTEGER", "INT")):
            length = self._column_type_length(column_type)
            if not length:
                if "UNSIGNED" in self._mysql_integer_type:
                    return self._mysql_integer_type
                return f"{self._mysql_integer_type}{' UNSIGNED' if unsigned else ''}"
            match = self._valid_column_type(self._mysql_integer_type)
            if match:
                if "UNSIGNED" in self._mysql_integer_type:
                    return f"{match.group(0).upper()}{length} UNSIGNED"
                return f"{match.group(0).upper()}{length}{' UNSIGNED' if unsigned else ''}"
        if data_type in {"BOOL", "BOOLEAN"}:
            return "TINYINT(1)"
        if data_type.startswith(("REAL", "DOUBLE", "FLOAT", "DECIMAL", "DEC", "FIXED")):
            return full_column_type
        if data_type not in MYSQL_COLUMN_TYPES:
            return self._mysql_string_type
        return full_column_type

    @staticmethod
    def _strip_wrapping_parentheses(expr: str) -> str:
        """Remove one or more layers of *fully wrapping* parentheses around an expression.

        Only strip if the matching ')' for the very first '(' is the final character
        of the string. This avoids corrupting expressions like "(a) + (b)".
        """
        s: str = expr.strip()
        while s.startswith("("):
            depth: int = 0
            match_idx: int = -1
            i: int
            ch: str
            # Find the matching ')' for the '(' at index 0
            for i, ch in enumerate(s):
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        match_idx = i
                        break
            # Only strip if the match closes at the very end
            if match_idx == len(s) - 1:
                s = s[1:match_idx].strip()
                # continue to try stripping more fully-wrapping layers
                continue
            # Not a fully-wrapped expression; stop
            break
        return s

    def _translate_default_for_mysql(self, column_type: str, default: str) -> str:
        """Translate SQLite DEFAULT expression to a MySQL-compatible one for common cases.

        Returns a string suitable to append after "DEFAULT ", without the word itself.
        Keeps literals as-is, maps `CURRENT_*`/`datetime('now')`/`strftime(...,'now')` to
        the appropriate MySQL `CURRENT_*` functions, preserves fractional seconds if the
        column type declares a precision, and normalizes booleans to 0/1.
        """
        raw: str = default.strip()
        if not raw:
            return raw

        s: str = self._strip_wrapping_parentheses(raw)
        u: str = s.upper()

        # NULL passthrough
        if u == "NULL":
            return "NULL"

        # Determine base data type
        match: t.Optional[re.Match[str]] = self._valid_column_type(column_type)
        base: str = match.group(0).upper() if match else column_type.upper()

        # TIMESTAMP: allow CURRENT_TIMESTAMP across versions; preserve FSP only if supported
        if base.startswith("TIMESTAMP") and (
            self.CURRENT_TS.match(s)
            or (self.SQLITE_NOW_FUNC.match(s) and s.lower().startswith("datetime"))
            or self.STRFTIME_NOW.match(s)
        ):
            len_match: t.Optional[re.Match[str]] = self.COLUMN_LENGTH_PATTERN.search(column_type)
            fsp: str = ""
            if self._allow_fsp and len_match:
                try:
                    n = int(len_match.group(0).strip("()"))
                except ValueError:
                    n = None
                if n is not None and 0 < n <= 6:
                    fsp = f"({n})"
            if "utc" in s.lower():
                return f"UTC_TIMESTAMP{fsp}"
            return f"CURRENT_TIMESTAMP{fsp}"

        # DATETIME: require server support, otherwise omit the DEFAULT
        if base.startswith("DATETIME") and (
            self.CURRENT_TS.match(s)
            or (self.SQLITE_NOW_FUNC.match(s) and s.lower().startswith("datetime"))
            or self.STRFTIME_NOW.match(s)
        ):
            if not self._allow_current_ts_dt:
                return ""
            len_match = self.COLUMN_LENGTH_PATTERN.search(column_type)
            fsp = ""
            if self._allow_fsp and len_match:
                try:
                    n = int(len_match.group(0).strip("()"))
                except ValueError:
                    n = None
                if n is not None and 0 < n <= 6:
                    fsp = f"({n})"
            if "utc" in s.lower():
                return f"UTC_TIMESTAMP{fsp}"
            return f"CURRENT_TIMESTAMP{fsp}"

        # DATE
        if (
            base.startswith("DATE")
            and (
                self.CURRENT_DATE.match(s)
                or self.CURRENT_TS.match(s)  # map CURRENT_TIMESTAMP → CURRENT_DATE for DATE
                or (self.SQLITE_NOW_FUNC.match(s) and s.lower().startswith("date"))
                or self.STRFTIME_NOW.match(s)
            )
            and self._allow_expr_defaults
        ):
            # Too old for expression defaults on DATE → fall back
            return "CURRENT_DATE"

        # TIME
        if (
            base.startswith("TIME")
            and (
                self.CURRENT_TIME.match(s)
                or self.CURRENT_TS.match(s)  # map CURRENT_TIMESTAMP → CURRENT_TIME for TIME
                or (self.SQLITE_NOW_FUNC.match(s) and s.lower().startswith("time"))
                or self.STRFTIME_NOW.match(s)
            )
            and self._allow_expr_defaults
        ):
            # Too old for expression defaults on TIME → fall back
            len_match = self.COLUMN_LENGTH_PATTERN.search(column_type)
            fsp = ""
            if self._allow_fsp and len_match:
                try:
                    n = int(len_match.group(0).strip("()"))
                except ValueError:
                    n = None
                if n is not None and 0 < n <= 6:
                    fsp = f"({n})"
            return f"UTC_TIME{fsp}" if "utc" in s.lower() else f"CURRENT_TIME{fsp}"

        # Booleans (store as 0/1)
        if base in {"BOOL", "BOOLEAN"} or base.startswith("TINYINT"):
            if u in {"TRUE", "'TRUE'", '"TRUE"'}:
                return "1"
            if u in {"FALSE", "'FALSE'", '"FALSE"'}:
                return "0"

        # Numeric literals (possibly wrapped)
        if self.NUMERIC_LITERAL_PATTERN.match(s):
            return s

        # Quoted strings and hex blobs pass through as-is
        if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')) or u.startswith("X'"):
            return s

        # Fallback: return stripped expression (MySQL 8.0.13+ allows expression defaults)
        if self._allow_expr_defaults:
            try:
                expr = sqlglot.parse_one(s, read="sqlite")
            except sqlglot_errors.ParseError:
                return s

            expr = expr.transform(self._rewrite_sqlite_view_functions)

            try:
                return expr.sql(dialect="mysql")
            except sqlglot_errors.SqlglotError:
                return s

        return s

    @classmethod
    def _column_type_length(cls, column_type: str, default: t.Optional[t.Union[str, int, float]] = None) -> str:
        suffix: t.Optional[t.Match[str]] = cls.COLUMN_LENGTH_PATTERN.search(column_type)
        if suffix:
            return suffix.group(0)
        if default is not None:
            return f"({default})"
        return ""

    @classmethod
    def _column_type_precision_and_scale(cls, column_type: str) -> str:
        suffix: t.Optional[t.Match[str]] = cls.COLUMN_PRECISION_AND_SCALE_PATTERN.search(column_type)
        if suffix:
            return suffix.group(0)
        return ""

    @classmethod
    def _translate_strftime_format(cls, fmt: str) -> str:
        converted: t.Optional[str] = sqlglot_format_time(
            fmt,
            SQLGLOT_MYSQL_INVERSE_TIME_MAPPING,
            SQLGLOT_MYSQL_INVERSE_TIME_TRIE,
        )
        return converted or fmt

    def _fetch_sqlite_master_rows(
        self,
        object_types: t.Sequence[str],
        include_sql: bool = False,
    ) -> t.List[t.Dict[str, t.Any]]:
        if not object_types:
            return []

        columns: t.List[str] = ["name", "type"]
        if include_sql:
            columns.append("sql")

        object_placeholders: str = ", ".join("?" * len(object_types))
        query: str = (
            """
            SELECT {columns}
            FROM sqlite_master
            WHERE type IN ({object_types})
            AND name NOT LIKE 'sqlite_%'
        """.format(
                columns=", ".join(columns),
                object_types=object_placeholders,
            )
        )
        params: t.List[t.Any] = list(object_types)

        if self._sqlite_tables:
            query += " AND name IN ({names})".format(
                names=", ".join("?" * len(self._sqlite_tables)),
            )
            params.extend(self._sqlite_tables)
        elif self._exclude_sqlite_tables:
            query += " AND name NOT IN ({names})".format(
                names=", ".join("?" * len(self._exclude_sqlite_tables)),
            )
            params.extend(self._exclude_sqlite_tables)

        self._sqlite_cur.execute(query, params)
        return [dict(row) for row in self._sqlite_cur.fetchall()]

    def _translate_sqlite_view_definition(self, view_name: str, view_sql: str) -> str:
        safe_name: str = safe_identifier_length(view_name)
        try:
            expression = sqlglot.parse_one(view_sql, read="sqlite")
        except sqlglot_errors.ParseError as err:
            raise ValueError(f"Unable to parse SQLite view {view_name!r}: {err}") from err

        expression.set("replace", True)
        expression.set("this", exp.to_identifier(safe_name))

        expression = expression.transform(self._rewrite_sqlite_view_functions)

        try:
            return expression.sql(dialect="mysql", identify=True)
        except sqlglot_errors.SqlglotError as err:
            raise ValueError(f"Unable to render MySQL view {view_name!r}: {err}") from err

    @classmethod
    def _rewrite_sqlite_view_functions(cls, node: exp.Expression) -> exp.Expression:
        def _is_now_literal(arg: exp.Expression) -> bool:
            return isinstance(arg, exp.Literal) and arg.is_string and str(arg.this).lower() == "now"

        def _extract_modifier(arguments: t.Sequence[exp.Expression]) -> t.Optional[str]:
            modifier: t.Optional[str] = None
            for arg in arguments[:2]:
                if isinstance(arg, exp.Literal) and arg.is_string:
                    value = str(arg.this).lower()
                    if value in {"utc", "localtime"}:
                        modifier = value
            return modifier

        def _current_datetime_expression(kind: str, modifier: t.Optional[str]) -> exp.Expression:
            if modifier == "utc":
                if kind == "DATETIME":
                    return exp.UtcTimestamp()
                if kind == "DATE":
                    return exp.Anonymous(this="UTC_DATE")
                return exp.UtcTime()
            if kind == "DATETIME":
                return exp.CurrentTimestamp()
            if kind == "DATE":
                return exp.CurrentDate()
            return exp.CurrentTime()

        if isinstance(node, exp.Anonymous):
            name: str = node.name.upper()
            args: t.Sequence[exp.Expression] = node.expressions or ()

            if name in {"DATETIME", "DATE", "TIME"} and args and _is_now_literal(args[0]):
                modifier: t.Optional[str] = _extract_modifier(args[1:])
                return _current_datetime_expression(name, modifier)

            if name == "STRFTIME" and len(args) >= 2 and isinstance(args[0], exp.Literal) and _is_now_literal(args[1]):
                mysql_format: str = cls._translate_strftime_format(str(args[0].this))
                # Optional modifiers follow the 'now' literal.
                modifier = _extract_modifier(args[2:])
                return exp.TimeToStr(
                    this=_current_datetime_expression("DATETIME", modifier),
                    format=exp.Literal.string(mysql_format),
                )
        elif isinstance(node, exp.TimeToStr):
            fmt: t.Optional[exp.Expression] = node.args.get("format")
            inner: exp.Expression = node.this
            if (
                isinstance(fmt, exp.Literal)
                and isinstance(inner, exp.TsOrDsToTimestamp)
                and isinstance(inner.this, exp.Literal)
                and inner.this.is_string
                and str(inner.this.this).lower() == "now"
            ):
                mysql_format = cls._translate_strftime_format(str(fmt.this))
                extra_args: t.List[exp.Expression] = []
                if isinstance(inner, exp.TsOrDsToTimestamp):
                    extra_args.extend(
                        value
                        for key, value in inner.args.items()
                        if key != "this" and isinstance(value, exp.Expression)
                    )
                    if getattr(inner, "expressions", None):
                        extra_args.extend(inner.expressions)
                modifier = _extract_modifier(extra_args)
                return exp.TimeToStr(
                    this=_current_datetime_expression("DATETIME", modifier),
                    format=exp.Literal.string(mysql_format),
                )
        return node

    def _create_mysql_view(self, view_name: str, view_sql: str) -> None:
        safe_name: str = safe_identifier_length(view_name)
        try:
            self._mysql_cur.execute(f"DROP TABLE IF EXISTS `{safe_name}`")
            self._mysql.commit()
        except mysql.connector.Error as err:
            if err.errno not in {
                errorcode.ER_BAD_TABLE_ERROR,
                errorcode.ER_WRONG_OBJECT,
                errorcode.ER_UNKNOWN_TABLE,
            }:
                raise

        # Ensure a stale VIEW does not block creation
        self._mysql_cur.execute(f"DROP VIEW IF EXISTS `{safe_name}`")
        self._mysql.commit()

        self._logger.info("Creating view %s", safe_name)
        self._mysql_cur.execute(view_sql)
        self._mysql.commit()

    def _create_table(self, table_name: str, transfer_rowid: bool = False, skip_default: bool = False) -> None:
        primary_keys: t.List[t.Dict[str, str]] = []

        sql: str = f"CREATE TABLE IF NOT EXISTS `{safe_identifier_length(table_name)}` ( "

        if transfer_rowid:
            sql += " `rowid` BIGINT NOT NULL, "

        quoted_table_name: str = self._sqlite_quote_ident(table_name)

        if self._sqlite_table_xinfo_support:
            self._sqlite_cur.execute(f'PRAGMA table_xinfo("{quoted_table_name}")')
        else:
            self._sqlite_cur.execute(f'PRAGMA table_info("{quoted_table_name}")')

        rows: t.List[t.Any] = self._sqlite_cur.fetchall()
        compound_primary_key: bool = len(tuple(True for row in rows if dict(row)["pk"] > 0)) > 1

        for row in rows:
            column: t.Dict[str, t.Any] = dict(row)
            mysql_safe_name: str = safe_identifier_length(column["name"])
            column_type: str = self._translate_type_from_sqlite_to_mysql(column["type"])

            # The "hidden" value is 0 for visible columns, 1 for "hidden" columns,
            # 2 for computed virtual columns and 3 for computed stored columns.
            # Read more on hidden columns here https://www.sqlite.org/pragma.html#pragma_table_xinfo
            if "hidden" in column and column["hidden"] == 1:
                continue

            auto_increment: bool = (
                column["pk"] > 0 and column_type.startswith(("INT", "BIGINT")) and not compound_primary_key
            )

            allow_expr_defaults: bool = getattr(self, "_allow_expr_defaults", False)
            is_mariadb: bool = getattr(self, "_is_mariadb", False)
            base_type: str = self._base_mysql_column_type(column_type)

            # Build DEFAULT clause safely (preserve falsy defaults like 0/'')
            default_clause: str = ""
            if (
                not skip_default
                and column["dflt_value"] is not None
                and self._column_type_supports_default(base_type, allow_expr_defaults)
                and not auto_increment
            ):
                td: str = self._translate_default_for_mysql(column_type, str(column["dflt_value"]))
                if td != "":
                    stripped_td: str = td.strip()
                    if base_type in MYSQL_TEXT_COLUMN_TYPES_WITH_JSON and stripped_td.upper() != "NULL":
                        td = self._format_textual_default(stripped_td, allow_expr_defaults, is_mariadb)
                    else:
                        td = stripped_td
                    default_clause = "DEFAULT " + td
            sql += " `{name}` {type} {notnull} {default} {auto_increment}, ".format(
                name=mysql_safe_name,
                type=column_type,
                notnull="NOT NULL" if column["notnull"] or column["pk"] else "NULL",
                auto_increment="AUTO_INCREMENT" if auto_increment else "",
                default=default_clause,
            )

            if column["pk"] > 0:
                primary_key: t.Dict[str, str] = {
                    "column": mysql_safe_name,
                    "length": "",
                }
                # In case we have a non-numeric primary key
                if column_type in (
                    MYSQL_TEXT_COLUMN_TYPES_WITH_JSON + MYSQL_BLOB_COLUMN_TYPES
                ) or column_type.startswith(("CHAR", "VARCHAR")):
                    primary_key["length"] = self._column_type_length(column_type, 255)
                primary_keys.append(primary_key)

        sql = sql.rstrip(", ")

        if len(primary_keys) > 0:
            sql += ", PRIMARY KEY ({columns})".format(
                columns=", ".join("`{column}`{length}".format(**primary_key) for primary_key in primary_keys)
            )

        if transfer_rowid:
            sql += f", CONSTRAINT `{safe_identifier_length(table_name)}_rowid` UNIQUE (`rowid`)"

        sql += f" ) ENGINE=InnoDB DEFAULT CHARSET={self._mysql_charset} COLLATE={self._mysql_collation}"

        try:
            self._mysql_cur.execute(sql)
            self._mysql.commit()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_INVALID_DEFAULT and not skip_default:
                self._logger.warning(
                    "MySQL failed creating table %s with DEFAULT values: %s. Retrying without DEFAULT values ...",
                    safe_identifier_length(table_name),
                    err,
                )
                return self._create_table(table_name, transfer_rowid, skip_default=True)
            else:
                self._logger.error(
                    "MySQL failed creating table %s: %s",
                    safe_identifier_length(table_name),
                    err,
                )
                raise

    def _truncate_table(self, table_name: str) -> None:
        self._mysql_cur.execute(
            """
            SELECT `TABLE_NAME`
            FROM `INFORMATION_SCHEMA`.`TABLES`
            WHERE `TABLE_SCHEMA` = %s
            AND `TABLE_NAME` = %s
            LIMIT 1
            """,
            (self._mysql_database, safe_identifier_length(table_name)),
        )
        if len(self._mysql_cur.fetchall()) > 0:
            self._logger.info("Truncating table %s", safe_identifier_length(table_name))
            self._mysql_cur.execute(f"TRUNCATE TABLE `{safe_identifier_length(table_name)}`")

    def _add_indices(self, table_name: str) -> None:
        quoted_table_name: str = self._sqlite_quote_ident(table_name)

        self._sqlite_cur.execute(f'PRAGMA table_info("{quoted_table_name}")')
        table_columns: t.Dict[str, str] = {}
        for row in self._sqlite_cur.fetchall():
            column: t.Dict[str, t.Any] = dict(row)
            table_columns[column["name"]] = column["type"]

        self._sqlite_cur.execute(f'PRAGMA index_list("{quoted_table_name}")')
        indices: t.Tuple[t.Dict[str, t.Any], ...] = tuple(dict(row) for row in self._sqlite_cur.fetchall())

        for index in indices:
            if index["origin"] == "pk":
                continue

            quoted_index_name: str = self._sqlite_quote_ident(index["name"])
            self._sqlite_cur.execute(f'PRAGMA index_info("{quoted_index_name}")')
            index_infos: t.Tuple[t.Dict[str, t.Any], ...] = tuple(dict(row) for row in self._sqlite_cur.fetchall())

            index_type: str = "UNIQUE" if int(index["unique"]) == 1 else "INDEX"

            try:
                if any(
                    table_columns[index_info["name"]].upper() in MYSQL_TEXT_COLUMN_TYPES_WITH_JSON
                    for index_info in index_infos
                ):
                    if self._use_fulltext and self._mysql_fulltext_support:
                        # Use fulltext if requested and available
                        index_type = "FULLTEXT"
                        index_columns: str = ",".join(
                            f'`{safe_identifier_length(index_info["name"])}`' for index_info in index_infos
                        )
                    else:
                        # Limit the max TEXT field index length to 255
                        index_columns = ", ".join(
                            "`{column}`{length}".format(
                                column=safe_identifier_length(index_info["name"]),
                                length=(
                                    "(255)"
                                    if table_columns[index_info["name"]].upper() in MYSQL_TEXT_COLUMN_TYPES_WITH_JSON
                                    else ""
                                ),
                            )
                            for index_info in index_infos
                        )
                else:
                    column_list: t.List[str] = []
                    for index_info in index_infos:
                        index_length: str = ""
                        # Limit the max BLOB field index length to 255
                        if table_columns[index_info["name"]].upper() in MYSQL_BLOB_COLUMN_TYPES:
                            index_length = "(255)"
                        else:
                            suffix: t.Optional[t.Match[str]] = self.COLUMN_LENGTH_PATTERN.search(
                                table_columns[index_info["name"]]
                            )
                            if suffix:
                                index_length = suffix.group(0)
                        column_list.append(f'`{safe_identifier_length(index_info["name"])}`{index_length}')
                    index_columns = ", ".join(column_list)
            except (KeyError, TypeError, IndexError, ValueError):
                self._logger.warning(
                    """Failed adding index to column "%s" in table %s: Column not found!""",
                    ", ".join(safe_identifier_length(index_info["name"]) for index_info in index_infos),
                    safe_identifier_length(table_name),
                )
                continue

            try:
                self._add_index(
                    table_name=table_name,
                    index_type=index_type,
                    index=index,
                    index_columns=index_columns,
                    index_infos=index_infos,
                )
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_BAD_FT_COLUMN and index_type == "FULLTEXT":
                    # handle bad FULLTEXT index
                    self._add_index(
                        table_name=table_name,
                        index_type="UNIQUE" if int(index["unique"]) == 1 else "INDEX",
                        index=index,
                        index_columns=", ".join(
                            "`{column}`{length}".format(
                                column=safe_identifier_length(index_info["name"]),
                                length=(
                                    "(255)"
                                    if table_columns[index_info["name"]].upper() in MYSQL_TEXT_COLUMN_TYPES_WITH_JSON
                                    else ""
                                ),
                            )
                            for index_info in index_infos
                        ),
                        index_infos=index_infos,
                    )
                else:
                    raise

    def _add_index(
        self,
        table_name: str,
        index_type: str,
        index: t.Dict[str, t.Any],
        index_columns: str,
        index_infos: t.Tuple[t.Dict[str, t.Any], ...],
        index_iteration: int = 0,
    ) -> None:
        sql: str = (
            """
            ALTER TABLE `{table}`
            ADD {index_type} `{name}`({columns})
        """.format(
                table=safe_identifier_length(table_name),
                index_type=index_type,
                name=(
                    safe_identifier_length(index["name"])
                    if index_iteration == 0
                    else f'{safe_identifier_length(index["name"], max_length=60)}_{index_iteration}'
                ),
                columns=index_columns,
            )
        )

        try:
            self._logger.info(
                """Adding %s to column "%s" in table %s""",
                "unique index" if int(index["unique"]) == 1 else "index",
                ", ".join(safe_identifier_length(index_info["name"]) for index_info in index_infos),
                safe_identifier_length(table_name),
            )
            self._mysql_cur.execute(sql)
            self._mysql.commit()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_DUP_KEYNAME:
                if not self._ignore_duplicate_keys:
                    # handle a duplicate key name
                    self._add_index(
                        table_name=table_name,
                        index_type=index_type,
                        index=index,
                        index_columns=index_columns,
                        index_infos=index_infos,
                        index_iteration=index_iteration + 1,
                    )
                    self._logger.warning(
                        """Duplicate key "%s" in table %s detected! Trying to create new key "%s_%s" ...""",
                        safe_identifier_length(index["name"]),
                        safe_identifier_length(table_name),
                        safe_identifier_length(index["name"]),
                        index_iteration + 1,
                    )
                else:
                    self._logger.warning(
                        """Ignoring duplicate key "%s" in table %s!""",
                        safe_identifier_length(index["name"]),
                        safe_identifier_length(table_name),
                    )
            elif err.errno == errorcode.ER_DUP_ENTRY:
                self._logger.warning(
                    """Ignoring duplicate entry when adding index to column "%s" in table %s!""",
                    ", ".join(safe_identifier_length(index_info["name"]) for index_info in index_infos),
                    safe_identifier_length(table_name),
                )
            elif err.errno == errorcode.ER_DUP_FIELDNAME:
                self._logger.warning(
                    """Failed adding index to column "%s" in table %s: Duplicate field name! Ignoring...""",
                    ", ".join(safe_identifier_length(index_info["name"]) for index_info in index_infos),
                    safe_identifier_length(table_name),
                )
            elif err.errno == errorcode.ER_TOO_MANY_KEYS:
                self._logger.warning(
                    """Failed adding index to column "%s" in table %s: Too many keys! Ignoring...""",
                    ", ".join(safe_identifier_length(index_info["name"]) for index_info in index_infos),
                    safe_identifier_length(table_name),
                )
            elif err.errno == errorcode.ER_TOO_LONG_KEY:
                self._logger.warning(
                    """Failed adding index to column "%s" in table %s: Key length too long! Ignoring...""",
                    ", ".join(safe_identifier_length(index_info["name"]) for index_info in index_infos),
                    safe_identifier_length(table_name),
                )
            elif err.errno == errorcode.ER_BAD_FT_COLUMN:
                # handle bad FULLTEXT index
                self._logger.warning(
                    """Failed adding FULLTEXT index to column "%s" in table %s. Retrying without FULLTEXT ...""",
                    ", ".join(safe_identifier_length(index_info["name"]) for index_info in index_infos),
                    safe_identifier_length(table_name),
                )
                raise
            else:
                self._logger.error(
                    """MySQL failed adding index to column "%s" in table %s: %s""",
                    ", ".join(safe_identifier_length(index_info["name"]) for index_info in index_infos),
                    safe_identifier_length(table_name),
                    err,
                )
                raise

    def _add_foreign_keys(self, table_name: str) -> None:
        quoted_table_name: str = self._sqlite_quote_ident(table_name)
        self._sqlite_cur.execute(f'PRAGMA foreign_key_list("{quoted_table_name}")')

        foreign_keys: t.Dict[int, t.List[t.Dict[str, t.Any]]] = {}
        for row in self._sqlite_cur.fetchall():
            foreign_key: t.Dict[str, t.Any] = dict(row)
            foreign_keys.setdefault(int(foreign_key["id"]), []).append(foreign_key)

        for fk_id, fk_rows in foreign_keys.items():
            fk_rows.sort(key=lambda fk_row: fk_row["seq"])
            ref_table: str = fk_rows[0]["table"]
            from_columns: t.List[str] = [safe_identifier_length(fk_row["from"]) for fk_row in fk_rows]

            referenced_columns: t.List[str]
            missing_references: t.List[t.Dict[str, t.Any]] = [fk_row for fk_row in fk_rows if not fk_row["to"]]
            if missing_references:
                if len(missing_references) != len(fk_rows):
                    self._logger.warning(
                        'Skipping foreign key "%s" in table %s: partially defined reference columns.',
                        safe_identifier_length(fk_rows[0]["from"]),
                        safe_identifier_length(table_name),
                    )
                    continue

                primary_keys: t.List[str] = self._get_table_primary_key_columns(ref_table)
                if not primary_keys or len(primary_keys) != len(from_columns):
                    self._logger.warning(
                        'Skipping foreign key "%s" in table %s: unable to resolve referenced primary key columns from table %s.',
                        safe_identifier_length(fk_rows[0]["from"]),
                        safe_identifier_length(table_name),
                        safe_identifier_length(ref_table),
                    )
                    continue
                referenced_columns = primary_keys
            else:
                referenced_columns = [safe_identifier_length(fk_row["to"]) for fk_row in fk_rows]

            sql = """
                ALTER TABLE `{table}`
                ADD CONSTRAINT `{table}_FK_{id}_{seq}`
                FOREIGN KEY ({columns})
                REFERENCES `{ref_table}`({ref_columns})
                ON DELETE {on_delete}
                ON UPDATE {on_update}
            """.format(
                id=fk_id,
                seq=fk_rows[0]["seq"],
                table=safe_identifier_length(table_name),
                columns=", ".join(f"`{column}`" for column in from_columns),
                ref_table=safe_identifier_length(ref_table),
                ref_columns=", ".join(f"`{column}`" for column in referenced_columns),
                on_delete=(
                    fk_rows[0]["on_delete"].upper() if fk_rows[0]["on_delete"].upper() != "SET DEFAULT" else "NO ACTION"
                ),
                on_update=(
                    fk_rows[0]["on_update"].upper() if fk_rows[0]["on_update"].upper() != "SET DEFAULT" else "NO ACTION"
                ),
            )

            try:
                self._logger.info(
                    "Adding foreign key to %s.(%s) referencing %s.(%s)",
                    safe_identifier_length(table_name),
                    ", ".join(from_columns),
                    safe_identifier_length(ref_table),
                    ", ".join(referenced_columns),
                )
                self._mysql_cur.execute(sql)
                self._mysql.commit()
            except mysql.connector.Error as err:
                self._logger.error(
                    "MySQL failed adding foreign key to %s.(%s) referencing %s.(%s): %s",
                    safe_identifier_length(table_name),
                    ", ".join(from_columns),
                    safe_identifier_length(ref_table),
                    ", ".join(referenced_columns),
                    err,
                )
                raise

    def _transfer_table_data(self, sql: str, total_records: int = 0) -> None:
        if self._chunk_size is not None and self._chunk_size > 0:
            for _ in trange(0, int(ceil(total_records / self._chunk_size)), disable=self._quiet):
                self._mysql_cur.executemany(
                    sql,
                    (tuple(row) for row in self._sqlite_cur.fetchmany(self._chunk_size)),  # type: ignore
                )
        else:
            self._mysql_cur.executemany(
                sql,
                (  # type: ignore
                    tuple(row)
                    for row in tqdm(
                        self._sqlite_cur.fetchall(),
                        total=total_records,
                        disable=self._quiet,
                    )
                ),
            )
        self._mysql.commit()

    def transfer(self) -> None:
        """The primary and only method with which we transfer all the data."""
        table_types: t.Tuple[str, ...] = ("table",)
        if self._sqlite_views_as_tables:
            table_types = (*table_types, "view")

        tables: t.List[t.Dict[str, t.Any]] = self._fetch_sqlite_master_rows(table_types)

        if not self._sqlite_views_as_tables and self._mysql_create_tables:
            views: t.List[t.Dict[str, t.Any]] = self._fetch_sqlite_master_rows(("view",), include_sql=True)
        else:
            views = []

        try:
            self._mysql_cur.execute("SET FOREIGN_KEY_CHECKS=0")

            for table in tables:
                table_name: str = table["name"]
                object_type: str = table.get("type", "table")
                quoted_table_name: str = self._sqlite_quote_ident(table_name)

                # check if we're transferring rowid
                transfer_rowid: bool = self._with_rowid and self._sqlite_table_has_rowid(table_name)

                # create the table
                if self._mysql_create_tables:
                    self._create_table(table_name, transfer_rowid=transfer_rowid)

                # truncate the table on request
                if self._mysql_truncate_tables:
                    self._truncate_table(table_name)

                # get the size of the data
                if self._mysql_transfer_data:
                    self._sqlite_cur.execute(f'SELECT COUNT(*) AS total_records FROM "{quoted_table_name}"')
                    total_records = int(dict(self._sqlite_cur.fetchone())["total_records"])
                else:
                    total_records = 0

                # only continue if there is anything to transfer
                if total_records > 0:
                    # populate it
                    self._logger.info(
                        "Transferring %s %s",
                        "view" if object_type == "view" else "table",
                        table_name,
                    )
                    if transfer_rowid:
                        select_list: str = 'rowid as "rowid", *'
                    else:
                        select_list = "*"
                    self._sqlite_cur.execute(f'SELECT {select_list} FROM "{quoted_table_name}"')
                    columns: t.List[str] = [
                        safe_identifier_length(column[0]) for column in self._sqlite_cur.description
                    ]
                    sql: str
                    if self._mysql_insert_method.upper() == "UPDATE":
                        sql = """
                            INSERT
                            INTO `{table}` ({fields})
                            {values_clause}
                            ON DUPLICATE KEY UPDATE {field_updates}
                        """.format(
                            table=safe_identifier_length(table_name),
                            fields=("`{}`, " * len(columns)).rstrip(" ,").format(*columns),
                            values_clause=(
                                "VALUES ({placeholders}) AS `__new__`"
                                if check_mysql_values_alias_support(self._mysql_version)
                                else "VALUES ({placeholders})"
                            ).format(placeholders=("%s, " * len(columns)).rstrip(" ,")),
                            field_updates=(
                                ("`{}`=`__new__`.`{}`, " * len(columns)).rstrip(" ,")
                                if check_mysql_values_alias_support(self._mysql_version)
                                else ("`{}`=`{}`, " * len(columns)).rstrip(" ,")
                            ).format(*list(chain.from_iterable((column, column) for column in columns))),
                        )
                    else:
                        sql = """
                            INSERT {ignore}
                            INTO `{table}` ({fields})
                            VALUES ({placeholders})
                        """.format(
                            ignore="IGNORE" if self._mysql_insert_method.upper() == "IGNORE" else "",
                            table=safe_identifier_length(table_name),
                            fields=("`{}`, " * len(columns)).rstrip(" ,").format(*columns),
                            placeholders=("%s, " * len(columns)).rstrip(" ,"),
                        )
                    try:
                        self._transfer_table_data(sql=sql, total_records=total_records)
                    except mysql.connector.Error as err:
                        self._logger.error(
                            "MySQL transfer failed inserting data into %s %s: %s",
                            "view" if object_type == "view" else "table",
                            safe_identifier_length(table_name),
                            err,
                        )
                        raise

                # add indices
                if self._mysql_create_tables:
                    self._add_indices(table_name)

                # add foreign keys
                if self._mysql_create_tables and not self._without_foreign_keys:
                    self._add_foreign_keys(table_name)

            if not self._sqlite_views_as_tables and self._mysql_create_tables:
                for view in views:
                    view_name: str = view["name"]
                    sql_definition: t.Optional[str] = view.get("sql")
                    if not sql_definition:
                        self._logger.warning(
                            "Skipping view %s: sqlite_master definition missing.",
                            safe_identifier_length(view_name),
                        )
                        continue
                    try:
                        mysql_view_sql: str = self._translate_sqlite_view_definition(view_name, sql_definition)
                        self._create_mysql_view(view_name, mysql_view_sql)
                    except ValueError as err:
                        self._logger.error(
                            "Failed translating view %s: %s",
                            safe_identifier_length(view_name),
                            err,
                        )
                        raise
                    except mysql.connector.Error as err:
                        self._logger.error(
                            "MySQL failed creating view %s: %s",
                            safe_identifier_length(view_name),
                            err,
                        )
                        raise
        except Exception:  # pylint: disable=W0706
            raise
        finally:
            self._mysql_cur.execute("SET FOREIGN_KEY_CHECKS=1")
        self._logger.info("Done!")
