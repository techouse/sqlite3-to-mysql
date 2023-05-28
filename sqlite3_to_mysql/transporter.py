"""Use to transfer an SQLite 3 database to MySQL."""

from __future__ import division

import logging
import re
import sqlite3
from datetime import timedelta
from decimal import Decimal
from itertools import chain
from math import ceil
from os.path import isfile, realpath
from sys import stdout

import mysql.connector
import six
from mysql.connector import (
    CharacterSet,
    __version__ as mysql_connector_version_string,
    errorcode,
)
from packaging import version
from tqdm import tqdm, trange

from sqlite3_to_mysql.sqlite_utils import (
    adapt_decimal,
    adapt_timedelta,
    convert_blob,
    convert_date,
    convert_decimal,
    convert_timedelta,
    unicase_compare,
    check_sqlite_table_xinfo_support,
)
from .mysql_utils import (
    MYSQL_BLOB_COLUMN_TYPES,
    MYSQL_COLUMN_TYPES,
    MYSQL_COLUMN_TYPES_WITHOUT_DEFAULT,
    MYSQL_INSERT_METHOD,
    MYSQL_TEXT_COLUMN_TYPES,
    MYSQL_TEXT_COLUMN_TYPES_WITH_JSON,
    check_mysql_fulltext_support,
    check_mysql_json_support,
    safe_identifier_length,
)

if six.PY2:
    from .sixeptions import *  # pylint: disable=W0622,W0401,W0614


class SQLite3toMySQL:
    """Use this class to transfer an SQLite 3 database to MySQL."""

    COLUMN_PATTERN = re.compile(r"^[^(]+")
    COLUMN_LENGTH_PATTERN = re.compile(r"\(\d+\)$")

    MYSQL_CONNECTOR_VERSION = version.parse(mysql_connector_version_string)

    def __init__(self, **kwargs):
        """Constructor."""
        if not kwargs.get("sqlite_file"):
            raise ValueError("Please provide an SQLite file")

        if not isfile(kwargs.get("sqlite_file")):
            raise FileNotFoundError("SQLite file does not exist")

        if not kwargs.get("mysql_user"):
            raise ValueError("Please provide a MySQL user")

        self._sqlite_file = realpath(kwargs.get("sqlite_file"))

        self._sqlite_tables = (
            tuple(kwargs.get("sqlite_tables"))
            if kwargs.get("sqlite_tables") is not None
            else tuple()
        )

        self._without_foreign_keys = (
            True
            if len(self._sqlite_tables) > 0
            else (kwargs.get("without_foreign_keys") or False)
        )

        self._mysql_user = str(kwargs.get("mysql_user"))

        self._mysql_password = (
            str(kwargs.get("mysql_password")) if kwargs.get("mysql_password") else None
        )

        self._mysql_host = str(kwargs.get("mysql_host") or "localhost")

        self._mysql_port = int(kwargs.get("mysql_port") or 3306)

        self._mysql_ssl_disabled = kwargs.get("mysql_ssl_disabled") or False

        self._chunk_size = int(kwargs.get("chunk")) if kwargs.get("chunk") else None

        self._quiet = kwargs.get("quiet") or False

        self._logger = self._setup_logger(
            log_file=kwargs.get("log_file") or None, quiet=self._quiet
        )

        self._mysql_database = str(kwargs.get("mysql_database") or "transfer")

        self._mysql_insert_method = str(
            kwargs.get("mysql_integer_type") or "IGNORE"
        ).upper()
        if self._mysql_insert_method not in MYSQL_INSERT_METHOD:
            self._mysql_insert_method = "IGNORE"

        self._mysql_truncate_tables = kwargs.get("mysql_truncate_tables") or False

        self._mysql_integer_type = str(
            kwargs.get("mysql_integer_type") or "INT(11)"
        ).upper()

        self._mysql_string_type = str(
            kwargs.get("mysql_string_type") or "VARCHAR(255)"
        ).upper()

        self._mysql_text_type = str(kwargs.get("mysql_text_type") or "TEXT").upper()
        if self._mysql_text_type not in MYSQL_TEXT_COLUMN_TYPES:
            self._mysql_text_type = "TEXT"

        self._mysql_charset = kwargs.get("mysql_charset") or "utf8mb4"

        self._mysql_collation = (
            kwargs.get("mysql_collation")
            or CharacterSet.get_default_collation(self._mysql_charset.lower())[0]
        )
        if (
            not kwargs.get("mysql_collation")
            and self._mysql_collation == "utf8mb4_0900_ai_ci"
        ):
            self._mysql_collation = "utf8mb4_general_ci"

        self.ignore_duplicate_keys = kwargs.get("ignore_duplicate_keys") or False

        self._use_fulltext = kwargs.get("use_fulltext") or False

        self._with_rowid = kwargs.get("with_rowid") or False

        sqlite3.register_adapter(Decimal, adapt_decimal)
        sqlite3.register_converter("DECIMAL", convert_decimal)
        sqlite3.register_adapter(timedelta, adapt_timedelta)
        sqlite3.register_converter("DATE", convert_date)
        sqlite3.register_converter("TIME", convert_timedelta)

        if six.PY2:
            sqlite3.register_converter("BLOB", convert_blob)

        self._sqlite = sqlite3.connect(
            realpath(self._sqlite_file), detect_types=sqlite3.PARSE_DECLTYPES
        )
        self._sqlite.row_factory = sqlite3.Row
        self._sqlite.create_collation("unicase", unicase_compare)

        self._sqlite_cur = self._sqlite.cursor()

        self._sqlite_version = self._get_sqlite_version()
        self._sqlite_table_xinfo_support = check_sqlite_table_xinfo_support(
            self._sqlite_version
        )

        try:
            self._mysql = mysql.connector.connect(
                user=self._mysql_user,
                password=self._mysql_password,
                host=self._mysql_host,
                port=self._mysql_port,
                ssl_disabled=self._mysql_ssl_disabled,
                use_pure=True,
            )
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
            self._mysql_json_support = check_mysql_json_support(self._mysql_version)
            self._mysql_fulltext_support = check_mysql_fulltext_support(
                self._mysql_version
            )

            if self._use_fulltext and not self._mysql_fulltext_support:
                raise ValueError(
                    "Your MySQL version does not support InnoDB FULLTEXT indexes!"
                )
        except mysql.connector.Error as err:
            self._logger.error(err)
            raise

    @classmethod
    def _setup_logger(cls, log_file=None, quiet=False):
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
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

    def _get_mysql_version(self):
        try:
            self._mysql_cur.execute("SHOW VARIABLES LIKE 'version'")
            return self._mysql_cur.fetchone()[1]
        except (IndexError, mysql.connector.Error) as err:
            self._logger.error(
                "MySQL failed checking for InnoDB version: %s",
                err,
            )
            raise

    def _get_sqlite_version(self):
        try:
            self._sqlite_cur.execute("SELECT sqlite_version()")
            return self._sqlite_cur.fetchone()[0]
        except (IndexError, sqlite3.Error) as err:
            self._logger.error(
                "SQLite failed checking for InnoDB version: %s",
                err,
            )
            raise

    def _sqlite_table_has_rowid(self, table):
        try:
            self._sqlite_cur.execute("""SELECT rowid FROM "{}" LIMIT 1""".format(table))
            self._sqlite_cur.fetchall()
            return True
        except sqlite3.OperationalError:
            return False

    def _create_database(self):
        try:
            self._mysql_cur.execute(
                """
                CREATE DATABASE IF NOT EXISTS `{database}`
                DEFAULT CHARACTER SET {charset}
                DEFAULT COLLATE {collation}
            """.format(
                    database=self._mysql_database,
                    charset=self._mysql_charset,
                    collation=self._mysql_collation,
                )
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
    def _valid_column_type(cls, column_type):
        return cls.COLUMN_PATTERN.match(column_type.strip())

    def _translate_type_from_sqlite_to_mysql(self, column_type):
        """This could be optimized even further, however is seems adequate."""
        full_column_type = column_type.upper()
        match = self._valid_column_type(column_type)
        if not match:
            raise ValueError("Invalid column_type!")

        data_type = match.group(0).upper()
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
            return match.group(0).upper() + length
        if data_type == "DOUBLE PRECISION":
            return "DOUBLE"
        if data_type == "UNSIGNED BIG INT":
            return "BIGINT" + self._column_type_length(column_type) + " UNSIGNED"
        if data_type in {"INT1", "INT2"}:
            return self._mysql_integer_type
        if data_type in {"INTEGER", "INT"}:
            length = self._column_type_length(column_type)
            if not length:
                return self._mysql_integer_type
            match = self._valid_column_type(self._mysql_integer_type)
            if self._mysql_integer_type.endswith("UNSIGNED"):
                return match.group(0).upper() + length + " UNSIGNED"
            return match.group(0).upper() + length
        if data_type in {"INT64", "NUMERIC"}:
            return "BIGINT" + self._column_type_length(column_type, 19)
        if data_type == "BOOLEAN":
            return "TINYINT(1)"
        if data_type not in MYSQL_COLUMN_TYPES:
            return self._mysql_string_type
        return full_column_type

    @classmethod
    def _column_type_length(cls, column_type, default=None):
        suffix = cls.COLUMN_LENGTH_PATTERN.search(column_type)
        if suffix:
            return suffix.group(0)
        if default:
            return "({})".format(default)
        return ""

    def _create_table(self, table_name, transfer_rowid=False):
        primary_keys = []

        sql = "CREATE TABLE IF NOT EXISTS `{}` ( ".format(
            safe_identifier_length(table_name)
        )

        if transfer_rowid:
            sql += " `rowid` BIGINT NOT NULL, "

        self._sqlite_cur.execute(
            'PRAGMA {command}("{table_name}")'.format(
                command="table_xinfo"
                if self._sqlite_table_xinfo_support
                else "table_info",
                table_name=table_name,
            )
        )

        rows = self._sqlite_cur.fetchall()
        compound_primary_key = (
            len(tuple(True for row in rows if dict(row)["pk"] > 0)) > 1
        )

        for row in rows:
            column = dict(row)
            mysql_safe_name = safe_identifier_length(column["name"])
            column_type = self._translate_type_from_sqlite_to_mysql(column["type"])

            # The "hidden" value is 0 for visible columns, 1 for "hidden" columns,
            # 2 for computed virtual columns and 3 for computed stored columns.
            # Read more on hidden columns here https://www.sqlite.org/pragma.html#pragma_table_xinfo
            if "hidden" in column and column["hidden"] == 1:
                continue

            sql += " `{name}` {type} {notnull} {default} {auto_increment}, ".format(
                name=mysql_safe_name,
                type=column_type,
                notnull="NOT NULL" if column["notnull"] or column["pk"] else "NULL",
                auto_increment="AUTO_INCREMENT"
                if column["pk"] > 0
                and column_type.startswith(("INT", "BIGINT"))
                and not compound_primary_key
                else "",
                default="DEFAULT " + column["dflt_value"]
                if column["dflt_value"]
                and column_type not in MYSQL_COLUMN_TYPES_WITHOUT_DEFAULT
                else "",
            )

            if column["pk"] > 0:
                primary_key = {
                    "column": mysql_safe_name,
                    "length": "",
                }
                # In case we have a non-numeric primary key
                if column_type in MYSQL_TEXT_COLUMN_TYPES_WITH_JSON.union(
                    MYSQL_BLOB_COLUMN_TYPES
                ) or column_type.startswith(("CHAR", "VARCHAR")):
                    primary_key["length"] = self._column_type_length(column_type, 255)
                primary_keys.append(primary_key)

        sql = sql.rstrip(", ")

        if len(primary_keys) > 0:
            sql += ", PRIMARY KEY ({columns})".format(
                columns=", ".join(
                    "`{column}`{length}".format(**primary_key)
                    for primary_key in primary_keys
                )
            )

        if transfer_rowid:
            sql += ", CONSTRAINT `{}_rowid` UNIQUE (`rowid`)".format(
                safe_identifier_length(table_name)
            )

        sql += " ) ENGINE=InnoDB DEFAULT CHARSET={charset} COLLATE={collation}".format(
            charset=self._mysql_charset,
            collation=self._mysql_collation,
        )

        try:
            self._mysql_cur.execute(sql)
            self._mysql.commit()
        except mysql.connector.Error as err:
            self._logger.error(
                "MySQL failed creating table %s: %s",
                safe_identifier_length(table_name),
                err,
            )
            raise

    def _truncate_table(self, table_name):
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
            self._mysql_cur.execute(
                "TRUNCATE TABLE `{}`".format(
                    safe_identifier_length(table_name),
                ),
            )

    def _add_indices(self, table_name):
        self._sqlite_cur.execute('PRAGMA table_info("{}")'.format(table_name))
        table_columns = {}
        for row in self._sqlite_cur.fetchall():
            column = dict(row)
            table_columns[column["name"]] = column["type"]

        self._sqlite_cur.execute('PRAGMA index_list("{}")'.format(table_name))
        indices = tuple(dict(row) for row in self._sqlite_cur.fetchall())

        for index in indices:
            if index["origin"] == "pk":
                continue

            self._sqlite_cur.execute('PRAGMA index_info("{}")'.format(index["name"]))
            index_infos = tuple(dict(row) for row in self._sqlite_cur.fetchall())

            index_type = "UNIQUE" if int(index["unique"]) == 1 else "INDEX"

            if any(
                table_columns[index_info["name"]].upper()
                in MYSQL_TEXT_COLUMN_TYPES_WITH_JSON
                for index_info in index_infos
            ):
                if self._use_fulltext and self._mysql_fulltext_support:
                    # Use fulltext if requested and available
                    index_type = "FULLTEXT"
                    index_columns = ",".join(
                        "`{}`".format(safe_identifier_length(index_info["name"]))
                        for index_info in index_infos
                    )
                else:
                    # Limit the max TEXT field index length to 255
                    index_columns = ", ".join(
                        "`{column}`{length}".format(
                            column=safe_identifier_length(index_info["name"]),
                            length="({})".format(255)
                            if table_columns[index_info["name"]].upper()
                            in MYSQL_TEXT_COLUMN_TYPES_WITH_JSON
                            else "",
                        )
                        for index_info in index_infos
                    )
            else:
                column_list = []
                for index_info in index_infos:
                    index_length = ""
                    # Limit the max BLOB field index length to 255
                    if (
                        table_columns[index_info["name"]].upper()
                        in MYSQL_BLOB_COLUMN_TYPES
                    ):
                        index_length = "({})".format(255)
                    else:
                        suffix = self.COLUMN_LENGTH_PATTERN.search(
                            table_columns[index_info["name"]]
                        )
                        if suffix:
                            index_length = suffix.group(0)
                    column_list.append(
                        "`{column}`{length}".format(
                            column=safe_identifier_length(index_info["name"]),
                            length=index_length,
                        )
                    )
                index_columns = ", ".join(column_list)

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
                                length="({})".format(255)
                                if table_columns[index_info["name"]].upper()
                                in MYSQL_TEXT_COLUMN_TYPES_WITH_JSON
                                else "",
                            )
                            for index_info in index_infos
                        ),
                        index_infos=index_infos,
                    )
                else:
                    raise

    def _add_index(
        self,
        table_name,
        index_type,
        index,
        index_columns,
        index_infos,
        index_iteration=0,
    ):
        sql = """
            ALTER TABLE `{table}`
            ADD {index_type} `{name}`({columns})
        """.format(
            table=safe_identifier_length(table_name),
            index_type=index_type,
            name=safe_identifier_length(index["name"])
            if index_iteration == 0
            else "{name}_{index_iteration}".format(
                name=safe_identifier_length(index["name"], max_length=60),
                index_iteration=index_iteration,
            ),
            columns=index_columns,
        )

        try:
            self._logger.info(
                """Adding %s to column "%s" in table %s""",
                "unique index" if int(index["unique"]) == 1 else "index",
                ", ".join(
                    safe_identifier_length(index_info["name"])
                    for index_info in index_infos
                ),
                safe_identifier_length(table_name),
            )
            self._mysql_cur.execute(sql)
            self._mysql.commit()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_DUP_KEYNAME:
                if not self.ignore_duplicate_keys:
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
            elif err.errno == errorcode.ER_BAD_FT_COLUMN:
                # handle bad FULLTEXT index
                self._logger.warning(
                    """Failed adding FULLTEXT index to column "%s" in table %s. Retrying without FULLTEXT ...""",
                    ", ".join(
                        safe_identifier_length(index_info["name"])
                        for index_info in index_infos
                    ),
                    safe_identifier_length(table_name),
                )
                raise
            else:
                self._logger.error(
                    """MySQL failed adding index to column "%s" in table %s: %s""",
                    ", ".join(
                        safe_identifier_length(index_info["name"])
                        for index_info in index_infos
                    ),
                    safe_identifier_length(table_name),
                    err,
                )
                raise

    def _add_foreign_keys(self, table_name):
        self._sqlite_cur.execute('PRAGMA foreign_key_list("{}")'.format(table_name))

        for row in self._sqlite_cur.fetchall():
            foreign_key = dict(row)
            sql = """
                ALTER TABLE `{table}`
                ADD CONSTRAINT `{table}_FK_{id}_{seq}`
                FOREIGN KEY (`{column}`)
                REFERENCES `{ref_table}`(`{ref_column}`)
                ON DELETE {on_delete}
                ON UPDATE {on_update}
            """.format(
                id=foreign_key["id"],
                seq=foreign_key["seq"],
                table=safe_identifier_length(table_name),
                column=safe_identifier_length(foreign_key["from"]),
                ref_table=safe_identifier_length(foreign_key["table"]),
                ref_column=safe_identifier_length(foreign_key["to"]),
                on_delete=foreign_key["on_delete"].upper()
                if foreign_key["on_delete"].upper() != "SET DEFAULT"
                else "NO ACTION",
                on_update=foreign_key["on_update"].upper()
                if foreign_key["on_update"].upper() != "SET DEFAULT"
                else "NO ACTION",
            )

            try:
                self._logger.info(
                    "Adding foreign key to %s.%s referencing %s.%s",
                    safe_identifier_length(table_name),
                    safe_identifier_length(foreign_key["from"]),
                    safe_identifier_length(foreign_key["table"]),
                    safe_identifier_length(foreign_key["to"]),
                )
                self._mysql_cur.execute(sql)
                self._mysql.commit()
            except mysql.connector.Error as err:
                self._logger.error(
                    "MySQL failed adding foreign key to %s.%s referencing %s.%s: %s",
                    safe_identifier_length(table_name),
                    safe_identifier_length(foreign_key["from"]),
                    safe_identifier_length(foreign_key["table"]),
                    safe_identifier_length(foreign_key["to"]),
                    err,
                )
                raise

    def _transfer_table_data(self, sql, total_records=0):
        if self._chunk_size is not None and self._chunk_size > 0:
            for _ in trange(
                0, int(ceil(total_records / self._chunk_size)), disable=self._quiet
            ):
                self._mysql_cur.executemany(
                    sql,
                    (
                        tuple(row)
                        for row in self._sqlite_cur.fetchmany(self._chunk_size)
                    ),
                )
        else:
            self._mysql_cur.executemany(
                sql,
                (
                    tuple(row)
                    for row in tqdm(
                        self._sqlite_cur.fetchall(),
                        total=total_records,
                        disable=self._quiet,
                    )
                ),
            )
        self._mysql.commit()

    def transfer(self):
        """The primary and only method with which we transfer all the data."""
        if len(self._sqlite_tables) > 0:
            # transfer only specific tables
            self._sqlite_cur.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table'
                AND name NOT LIKE 'sqlite_%'
                AND name IN({placeholders})
                """.format(
                    placeholders=("?, " * len(self._sqlite_tables)).rstrip(" ,")
                ),
                self._sqlite_tables,
            )
        else:
            # transfer all tables
            self._sqlite_cur.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table'
                AND name NOT LIKE 'sqlite_%'
                """
            )
        try:
            self._mysql_cur.execute("SET FOREIGN_KEY_CHECKS=0")

            for row in self._sqlite_cur.fetchall():
                table = dict(row)

                # check if we're transferring rowid
                transfer_rowid = self._with_rowid and self._sqlite_table_has_rowid(
                    table["name"]
                )

                # create the table
                self._create_table(table["name"], transfer_rowid=transfer_rowid)

                # truncate the table on request
                if self._mysql_truncate_tables:
                    self._truncate_table(table["name"])

                # get the size of the data
                self._sqlite_cur.execute(
                    'SELECT COUNT(*) AS total_records FROM "{}"'.format(table["name"])
                )
                total_records = int(dict(self._sqlite_cur.fetchone())["total_records"])

                # only continue if there is anything to transfer
                if total_records > 0:
                    # populate it
                    self._logger.info("Transferring table %s", table["name"])
                    self._sqlite_cur.execute(
                        """
                        SELECT {rowid} * FROM "{table_name}"
                    """.format(
                            rowid='rowid as "rowid",' if transfer_rowid else "",
                            table_name=table["name"],
                        )
                    )
                    columns = [
                        safe_identifier_length(column[0])
                        for column in self._sqlite_cur.description
                    ]
                    if self._mysql_insert_method.upper() == "UPDATE":
                        sql = """
                            INSERT
                            INTO `{table}` ({fields})
                            VALUES ({placeholders}) AS `__new__`
                            ON DUPLICATE KEY UPDATE {field_updates}
                        """.format(
                            table=safe_identifier_length(table["name"]),
                            fields=("`{}`, " * len(columns))
                            .rstrip(" ,")
                            .format(*columns),
                            placeholders=("%s, " * len(columns)).rstrip(" ,"),
                            field_updates=("`{}`=`__new__`.`{}`, " * len(columns))
                            .rstrip(" ,")
                            .format(
                                *list(
                                    chain.from_iterable(
                                        (column, column) for column in columns
                                    )
                                )
                            ),
                        )
                    else:
                        sql = """
                            INSERT {ignore}
                            INTO `{table}` ({fields})
                            VALUES ({placeholders})
                        """.format(
                            ignore="IGNORE"
                            if self._mysql_insert_method.upper() == "IGNORE"
                            else "",
                            table=safe_identifier_length(table["name"]),
                            fields=("`{}`, " * len(columns))
                            .rstrip(" ,")
                            .format(*columns),
                            placeholders=("%s, " * len(columns)).rstrip(" ,"),
                        )
                    try:
                        self._transfer_table_data(sql=sql, total_records=total_records)
                    except mysql.connector.Error as err:
                        self._logger.error(
                            "MySQL transfer failed inserting data into table %s: %s",
                            safe_identifier_length(table["name"]),
                            err,
                        )
                        raise

                # add indices
                self._add_indices(table["name"])

                # add foreign keys
                if not self._without_foreign_keys:
                    self._add_foreign_keys(table["name"])
        except Exception:  # pylint: disable=W0706
            raise
        finally:
            self._mysql_cur.execute("SET FOREIGN_KEY_CHECKS=1")
        self._logger.info("Done!")
