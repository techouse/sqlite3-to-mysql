#!/usr/bin/env python
import sys

from src.sqlite3_to_mysql import SQLite3toMySQL

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--sqlite-file",
        dest="sqlite_file",
        default=None,
        help="SQLite3 db file",
        required=True,
    )
    parser.add_argument(
        "-u",
        "--mysql-user",
        dest="mysql_user",
        default=None,
        help="MySQL user",
        required=True,
    )
    parser.add_argument(
        "-p",
        "--mysql-password",
        dest="mysql_password",
        default=None,
        help="MySQL password",
    )
    parser.add_argument(
        "-d",
        "--mysql-database",
        dest="mysql_database",
        default=None,
        help="MySQL database name",
        required=True,
    )
    parser.add_argument(
        "-H", "--mysql-host", dest="mysql_host", default="localhost", help="MySQL host"
    )
    parser.add_argument(
        "-P",
        "--mysql-port",
        dest="mysql_port",
        type=int,
        default=3306,
        help="MySQL port",
    )
    parser.add_argument(
        "--mysql-integer-type",
        dest="mysql_integer_type",
        default="INT(11)",
        help="MySQL default integer field type",
    )
    parser.add_argument(
        "--mysql-string-type",
        dest="mysql_string_type",
        default="VARCHAR(255)",
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

    try:
        converter = SQLite3toMySQL(
            sqlite_file=args.sqlite_file,
            mysql_user=args.mysql_user,
            mysql_password=args.mysql_password,
            mysql_database=args.mysql_database,
            mysql_host=args.mysql_host,
            mysql_port=args.mysql_port,
            mysql_integer_type=args.mysql_integer_type,
            mysql_string_type=args.mysql_string_type,
            chunk=args.chunk,
            log_file=args.log_file,
        )
        converter.transfer()
    except KeyboardInterrupt:
        print("Exiting ...")
        sys.exit(1)
    except Exception as err:
        print(err)
        sys.exit(1)
