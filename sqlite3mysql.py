#!/usr/bin/env python3
import logging
import sqlite3
import sys
import re
from math import ceil
from os.path import realpath, isfile

import mysql.connector
from mysql.connector import errorcode
from tqdm import tqdm


class SQLite3toMySQL:
    """
    Use this class to transfer an SQLite 3 database to MySQL.
    """

    def __init__(self, **kwargs):
        if not isfile(kwargs.get("sqlite_file", None)):
            print("SQLite file does not exist!")
            sys.exit(1)

        if kwargs.get("mysql_user", None) is None:
            print("Please provide a MySQL user!")
            sys.exit(1)

        if kwargs.get("mysql_password", None) is None:
            print("Please provide a MySQL password")
            sys.exit(1)

        self._chunk_size = kwargs.get("chunk", None)
        if self._chunk_size:
            self._chunk_size = int(self._chunk_size)

        self._logger = self._setup_logger(log_file=kwargs.get("log_file", None))

        self._mysql_database = kwargs.get("mysql_database", "transfer")

        self._mysql_integer_type = kwargs.get("mysql_integer_type", "int(11)")

        self._mysql_string_type = kwargs.get("mysql_string_type", "varchar(300)")

        self._sqlite = sqlite3.connect(kwargs.get("sqlite_file", None))
        self._sqlite.row_factory = sqlite3.Row

        self._sqlite_cur = self._sqlite.cursor()

        self._mysql = mysql.connector.connect(
            user=kwargs.get("mysql_user", None),
            password=kwargs.get("mysql_password", None),
            host=kwargs.get("mysql_host", "localhost"),
            use_pure=True,
        )
        self._mysql_cur = self._mysql.cursor(prepared=True)
        try:
            self._mysql.database = self._mysql_database
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                self._create_database()
            else:
                self._logger.error(err)
                sys.exit(1)

    @classmethod
    def _setup_logger(cls, log_file=None):
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        screen_handler = logging.StreamHandler(stream=sys.stdout)
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
                "CREATE DATABASE IF NOT EXISTS `{}` DEFAULT CHARACTER SET 'utf8'".format(
                    self._mysql_database
                )
            )
            self._mysql_cur.close()
            self._mysql.commit()
            self._mysql.database = self._mysql_database
            self._mysql_cur = self._mysql.cursor(prepared=True)
        except mysql.connector.Error as err:
            self._logger.error(
                "_create_database failed creating databse {}: {}".format(
                    self._mysql_database, err
                )
            )
            sys.exit(1)

    def _translate_type_from_sqlite_to_mysql(self, column_type):
        """
        This method could be optimized even further, however at the time
        of writing it seemed adequate enough.
        """
        full_column_type = column_type.upper()
        match = re.match(r"^[^(]+", column_type.strip())
        if not match:
            raise ValueError("Invalid column_type!")

        column_type = match.group(0).upper()
        if column_type in {"TEXT", "CLOB"}:
            return "TEXT"
        elif column_type == "CHARACTER":
            return "CHAR" + self._column_type_length(column_type)
        elif column_type == "NCHAR":
            return "CHAR" + self._column_type_length(column_type)
        elif column_type == "NATIVE CHARACTER":
            return "CHAR" + self._column_type_length(column_type)
        elif column_type == "VARYING CHARACTER":
            return "VARCHAR" + self._column_type_length(column_type, 255)
        elif column_type == "NVARCHAR":
            return "VARCHAR" + self._column_type_length(column_type, 255)
        elif column_type == "VARCHAR":
            return "VARCHAR" + self._column_type_length(column_type, 255)
        elif column_type == "DOUBLE PRECISION":
            return "DOUBLE"
        elif column_type == "UNSIGNED BIG INT":
            return "BIGINT" + self._column_type_length(column_type) + " UNSIGNED"
        elif column_type in {"INT1", "INT2"}:
            return "INT"
        else:
            return full_column_type

    @staticmethod
    def _column_type_length(column_type, default=None):
        suffix = re.search(r"\(\d+\)$", column_type)
        if suffix:
            return suffix.group(0)
        elif default:
            return "({})".format(default)
        else:
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
        sql += " ) ENGINE = InnoDB CHARACTER SET utf8"
        sql = " ".join(sql.split())

        try:
            self._mysql_cur.execute(sql)
            self._mysql.commit()
        except mysql.connector.Error as err:
            self._logger.error(
                "_create_table failed creating table {}: {}".format(table_name, err)
            )
            sys.exit(1)

    def _transfer_table_data(self, sql, total_records=0):
        if self._chunk_size is not None and self._chunk_size > 0:
            for _ in tqdm(range(0, ceil(total_records / self._chunk_size))):
                self._mysql_cur.executemany(
                    sql,
                    (
                        tuple(row)
                        for row in self._sqlite_cur.fetchmany(self._chunk_size)
                    ),
                )
                self._mysql.commit()
        else:
            self._mysql_cur.executemany(
                sql, (tuple(row) for row in self._sqlite_cur.fetchall())
            )
            self._mysql.commit()

    def transfer(self):
        """
        The primary and only method with which we transfer the data
        """
        self._sqlite_cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
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
                self._logger.info("Transferring table {}".format(table["name"]))
                self._sqlite_cur.execute('SELECT * FROM "{}"'.format(table["name"]))
                columns = [column[0] for column in self._sqlite_cur.description]
                sql = "INSERT IGNORE INTO `{table}` ({fields}) VALUES ({placeholders})".format(
                    table=table["name"],
                    fields=("`{}`, " * len(columns)).rstrip(" ,").format(*columns),
                    placeholders=("%s, " * len(columns)).rstrip(" ,"),
                )
                try:
                    self._transfer_table_data(sql=sql, total_records=total_records)
                except mysql.connector.Error as err:
                    self._logger.error(
                        "transfer failed inserting data into table {}: {}".format(
                            table["name"], err
                        )
                    )
                    sys.exit(1)
        self._logger.info("Done!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f", "--sqlite-file", dest="sqlite_file", default=None, help="SQLite3 db file"
    )
    parser.add_argument(
        "-u", "--mysql-user", dest="mysql_user", default=None, help="MySQL user"
    )
    parser.add_argument(
        "-p",
        "--mysql-password",
        dest="mysql_password",
        default=None,
        help="MySQL password",
    )
    parser.add_argument(
        "-d", "--mysql-database", dest="mysql_database", default=None, help="MySQL host"
    )
    parser.add_argument(
        "--mysql-host", dest="mysql_host", default="localhost", help="MySQL host"
    )
    parser.add_argument(
        "--mysql-integer-type",
        dest="mysql_integer_type",
        default="int(11)",
        help="MySQL default integer field type",
    )
    parser.add_argument(
        "--mysql-string-type",
        dest="mysql_string_type",
        default="varchar(300)",
        help="MySQL default string field type",
    )
    parser.add_argument(
        "-c",
        "--chunk",
        dest="chunk",
        type=int,
        default=None,
        help="Chunk reading/writing SQL records",
    )
    parser.add_argument("-l", "--log-file", dest="log_file", help="Log file")
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    converter = SQLite3toMySQL(
        sqlite_file=args.sqlite_file,
        mysql_user=args.mysql_user,
        mysql_password=args.mysql_password,
        mysql_database=args.mysql_database,
        mysql_host=args.mysql_host,
        mysql_integer_type=args.mysql_integer_type,
        mysql_string_type=args.mysql_string_type,
        chunk=args.chunk,
        log_file=args.log_file,
    )
    converter.transfer()
