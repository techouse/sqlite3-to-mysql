"""Use to transfer an SQLite 3 database to MySQL."""

from __future__ import division

import logging
import re
import sqlite3
from datetime import timedelta
from decimal import Decimal
from math import ceil
from os.path import isfile, realpath
from sys import stdout

import mysql.connector
import six
from mysql.connector import errorcode  # pylint: disable=C0412
from tqdm import trange

from sqlite3_to_mysql.sqlite_utils import (  # noqa: ignore=I100
    adapt_decimal,
    adapt_timedelta,
    convert_decimal,
    convert_timedelta,
    convert_blob,
)

if six.PY2:
    from .sixeptions import *  # pylint: disable=W0622,W0401,W0614


class SQLite3toMySQL:  # pylint: disable=R0902,R0903
    """Use this class to transfer an SQLite 3 database to MySQL."""

    COLUMN_PATTERN = re.compile(r"^[^(]+")
    COLUMN_LENGTH_PATTERN = re.compile(r"\(\d+\)$")

    def __init__(self, **kwargs):  # noqa: ignore=C901 pylint: disable=R0912
        """Constructor."""
        if not kwargs.get("sqlite_file"):
            raise ValueError("Please provide an SQLite file")

        if not isfile(kwargs.get("sqlite_file")):
            raise FileNotFoundError("SQLite file does not exist")

        if not kwargs.get("mysql_user"):
            raise ValueError("Please provide a MySQL user")

        self._sqlite_file = realpath(kwargs.get("sqlite_file"))

        self._mysql_user = str(kwargs.get("mysql_user"))

        self._mysql_password = (
            str(kwargs.get("mysql_password")) if kwargs.get("mysql_password") else None
        )

        self._mysql_host = str(kwargs.get("mysql_host") or "localhost")

        self._mysql_port = int(kwargs.get("mysql_port") or 3306)

        self._chunk_size = int(kwargs.get("chunk")) if kwargs.get("chunk") else None

        self._logger = self._setup_logger(log_file=kwargs.get("log_file") or None)

        self._mysql_database = str(kwargs.get("mysql_database") or "transfer")

        self._mysql_integer_type = str(
            kwargs.get("mysql_integer_type") or "INT(11)"
        ).upper()

        self._mysql_string_type = str(
            kwargs.get("mysql_string_type") or "VARCHAR(255)"
        ).upper()

        sqlite3.register_adapter(Decimal, adapt_decimal)
        sqlite3.register_converter("DECIMAL", convert_decimal)
        sqlite3.register_adapter(timedelta, adapt_timedelta)
        sqlite3.register_converter("TIME", convert_timedelta)

        if six.PY2:
            sqlite3.register_converter("BLOB", convert_blob)

        self._sqlite = sqlite3.connect(
            realpath(self._sqlite_file), detect_types=sqlite3.PARSE_DECLTYPES
        )
        self._sqlite.row_factory = sqlite3.Row

        self._sqlite_cur = self._sqlite.cursor()

        try:
            self._mysql = mysql.connector.connect(
                user=self._mysql_user,
                password=self._mysql_password,
                host=self._mysql_host,
                port=self._mysql_port,
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
        except mysql.connector.Error as err:
            self._logger.error(err)
            raise

    @classmethod
    def _setup_logger(cls, log_file=None):
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        screen_handler = logging.StreamHandler(stream=stdout)
        screen_handler.setFormatter(formatter)
        logger = logging.getLogger(cls.__name__)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(screen_handler)

        if log_file:
            file_handler = logging.FileHandler(realpath(log_file), mode="w")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def _create_database(self):
        try:
            self._mysql_cur.execute(
                "CREATE DATABASE IF NOT EXISTS `{}` DEFAULT CHARACTER SET 'utf8mb4'".format(  # noqa: ignore=E501 pylint: disable=C0301
                    self._mysql_database
                )
            )
            self._mysql_cur.close()
            self._mysql.commit()
            self._mysql.database = self._mysql_database
            self._mysql_cur = self._mysql.cursor(prepared=True)
        except mysql.connector.Error as err:
            self._logger.error(
                "_create_database failed creating databse %s: %s",
                self._mysql_database,
                err,
            )
            raise

    @classmethod
    def _valid_column_type(cls, column_type):
        return cls.COLUMN_PATTERN.match(column_type.strip())

    def _translate_type_from_sqlite_to_mysql(  # noqa: ignore=C901 pylint: disable=C0330
        self, column_type
    ):  # pylint: disable=R0911,R0912
        """This could be optimized even further, however is seems adequate."""
        full_column_type = column_type.upper()
        match = self._valid_column_type(column_type)
        if not match:
            raise ValueError("Invalid column_type!")

        data_type = match.group(0).upper()
        if data_type in {"TEXT", "CLOB"}:
            return "TEXT"
        if data_type in {"CHARACTER", "NCHAR", "NATIVE CHARACTER"}:
            return "CHAR" + self._column_type_length(column_type)
        if data_type in {"VARYING CHARACTER", "NVARCHAR", "VARCHAR"}:
            if self._mysql_string_type == "TEXT":
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
        if data_type == "NUMERIC":
            return "BIGINT" + self._column_type_length(column_type, 19)
        return full_column_type

    @classmethod
    def _column_type_length(cls, column_type, default=None):
        suffix = cls.COLUMN_LENGTH_PATTERN.search(column_type)
        if suffix:
            return suffix.group(0)
        if default:
            return "({})".format(default)
        return ""

    def _create_table(self, table_name):
        primary_key = ""

        sql = "CREATE TABLE IF NOT EXISTS `{}` ( ".format(table_name)

        self._sqlite_cur.execute('PRAGMA table_info("{}")'.format(table_name))

        for row in self._sqlite_cur.fetchall():
            column = dict(row)
            sql += " `{name}` {type} {notnull} {auto_increment}, ".format(
                name=column["name"],
                type=self._translate_type_from_sqlite_to_mysql(column["type"]),
                notnull="NOT NULL" if column["notnull"] else "NULL",
                auto_increment="AUTO_INCREMENT"
                if column["pk"]
                and self._translate_type_from_sqlite_to_mysql(column["type"])
                in {"INT", "BIGINT"}
                else "",
            )
            if column["pk"]:
                primary_key = column["name"]

        sql = sql.rstrip(", ")
        if primary_key:
            sql += ", PRIMARY KEY (`{}`)".format(primary_key)
        sql += " ) ENGINE = InnoDB CHARACTER SET utf8mb4"

        try:
            self._mysql_cur.execute(sql)
            self._mysql.commit()
        except mysql.connector.Error as err:
            self._logger.error(
                "_create_table failed creating table %s: %s", table_name, err
            )
            raise

    def _add_indices(self, table_name):  # pylint: disable=R0914
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
                table_columns[index_info["name"]].upper()  # pylint: disable=C0330
                == "TEXT"  # pylint: disable=C0330
                for index_info in index_infos  # noqa: ignore=E501 pylint: disable=C0330
            ):
                # Limit the max TEXT field index length to 255
                index_type = "FULLTEXT"
                index_columns = ",".join(
                    "`{}`".format(index_info["name"]) for index_info in index_infos
                )
            else:
                column_list = []
                for index_info in index_infos:
                    index_length = ""
                    if table_columns[index_info["name"]].upper() == "BLOB":
                        index_length = "({})".format(255)
                    else:
                        suffix = self.COLUMN_LENGTH_PATTERN.search(
                            table_columns[index_info["name"]]
                        )
                        if suffix:
                            index_length = suffix.group(0)
                    column_list.append(
                        "`{column}`{length}".format(
                            column=index_info["name"], length=index_length
                        )
                    )
                index_columns = ", ".join(column_list)

            sql = """
                ALTER TABLE `{table}`
                ADD {index_type} `{name}`({columns})
            """.format(
                table=table_name,
                index_type=index_type,
                name=index["name"],
                columns=index_columns,
            )

            try:
                self._logger.info(
                    """Adding %s to column "%s" in table %s""",
                    "unique index" if int(index["unique"]) == 1 else "index",
                    ", ".join(index_info["name"] for index_info in index_infos),
                    table_name,
                )
                self._mysql_cur.execute(sql)
                self._mysql.commit()
            except mysql.connector.Error as err:
                self._logger.error(
                    "_add_indices failed adding indices to table %s: %s",
                    table_name,
                    err,
                )
                raise

    def _add_foreign_keys(self, table_name):
        self._sqlite_cur.execute('PRAGMA foreign_key_list("{}")'.format(table_name))

        for row in self._sqlite_cur.fetchall():
            foreign_key = dict(row)
            sql = """
                ALTER TABLE `{table}`
                ADD CONSTRAINT {table}_FK_{id}_{seq}
                FOREIGN KEY (`{column}`)
                REFERENCES `{ref_table}`(`{ref_column}`)
                ON DELETE {on_delete}
                ON UPDATE {on_update}
            """.format(
                id=foreign_key["id"],
                seq=foreign_key["seq"],
                table=table_name,
                column=foreign_key["from"],
                ref_table=foreign_key["table"],
                ref_column=foreign_key["to"],
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
                    table_name,
                    foreign_key["from"],
                    foreign_key["table"],
                    foreign_key["to"],
                )
                self._mysql_cur.execute(sql)
                self._mysql.commit()
            except mysql.connector.Error as err:
                self._logger.error(
                    "_add_foreign_keys failed adding foreign keys to table %s: %s",
                    table_name,
                    err,
                )
                raise

    def _transfer_table_data(self, sql, total_records=0):
        if self._chunk_size is not None and self._chunk_size > 0:
            for _ in trange(0, int(ceil(total_records / self._chunk_size))):
                self._mysql_cur.executemany(
                    sql,
                    (
                        tuple(row)
                        for row in self._sqlite_cur.fetchmany(self._chunk_size)
                    ),
                )
        else:
            self._mysql_cur.executemany(
                sql, (tuple(row) for row in self._sqlite_cur.fetchall())
            )
        self._mysql.commit()

    def transfer(self):
        """The primary and only method with which we transfer all the data."""
        self._sqlite_cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"  # noqa: ignore=E501 pylint: disable=C0301
        )
        try:
            self._mysql_cur.execute("SET FOREIGN_KEY_CHECKS=0")

            for row in self._sqlite_cur.fetchall():
                table = dict(row)

                # create the table
                self._create_table(table["name"])

                # get the size of the data
                self._sqlite_cur.execute(
                    'SELECT COUNT(*) AS total_records FROM "{}"'.format(table["name"])
                )
                total_records = int(dict(self._sqlite_cur.fetchone())["total_records"])

                # only continue if there is anything to transfer
                if total_records > 0:
                    # populate it
                    self._logger.info("Transferring table %s", table["name"])
                    self._sqlite_cur.execute('SELECT * FROM "{}"'.format(table["name"]))
                    columns = [column[0] for column in self._sqlite_cur.description]
                    sql = "INSERT IGNORE INTO `{table}` ({fields}) VALUES ({placeholders})".format(  # noqa: ignore=E501 pylint: disable=C0301
                        table=table["name"],
                        fields=("`{}`, " * len(columns)).rstrip(" ,").format(*columns),
                        placeholders=("%s, " * len(columns)).rstrip(" ,"),
                    )
                    try:
                        self._transfer_table_data(sql=sql, total_records=total_records)
                    except mysql.connector.Error as err:
                        self._logger.error(
                            "transfer failed inserting data into table %s: %s",
                            table["name"],
                            err,
                        )
                        raise

                # add indices
                self._add_indices(table["name"])

                # add foreign keys
                self._add_foreign_keys(table["name"])
        except Exception:  # pylint: disable=W0706
            raise
        finally:
            self._mysql_cur.execute("SET FOREIGN_KEY_CHECKS=1")
        self._logger.info("Done!")
