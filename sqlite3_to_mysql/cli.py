"""The command line interface of SQLite3toMySQL."""

import sys

import click
from sqlite3_to_mysql import SQLite3toMySQL


@click.command()
@click.option(
    "-f",
    "--sqlite-file",
    type=click.Path(exists=True),
    default=None,
    help="SQLite3 database file",
    required=True,
)
@click.option(
    "-d", "--mysql-database", default=None, help="MySQL database name", required=True
)
@click.option("-u", "--mysql-user", default=None, help="MySQL user", required=True)
@click.option("-p", "--mysql-password", default=None, help="MySQL password")
@click.option(
    "-h", "--mysql-host", default="localhost", help="MySQL host. Defaults to localhost."
)
@click.option(
    "-P", "--mysql-port", type=int, default=3306, help="MySQL port. Defaults to 3306."
)
@click.option(
    "--mysql-integer-type",
    default="INT(11)",
    help="MySQL default integer field type. Defaults to INT(11).",
)
@click.option(
    "--mysql-string-type",
    default="VARCHAR(255)",
    help="MySQL default string field type. Defaults to VARCHAR(255).",
)
@click.option(
    "-c", "--chunk", type=int, default=None, help="Chunk reading/writing SQL records"
)
@click.option("-l", "--log-file", type=click.Path(), help="Log file")
def cli(  # noqa: ignore=C0330  # pylint: disable=C0330,R0913
    sqlite_file,
    mysql_user,
    mysql_password,
    mysql_database,
    mysql_host,
    mysql_port,
    mysql_integer_type,
    mysql_string_type,
    chunk,
    log_file,
):
    """Transfer SQLite to MySQL using the provided CLI options."""
    try:
        converter = SQLite3toMySQL(
            sqlite_file=sqlite_file,
            mysql_user=mysql_user,
            mysql_password=mysql_password,
            mysql_database=mysql_database,
            mysql_host=mysql_host,
            mysql_port=mysql_port,
            mysql_integer_type=mysql_integer_type,
            mysql_string_type=mysql_string_type,
            chunk=chunk,
            log_file=log_file,
        )
        converter.transfer()
    except KeyboardInterrupt:
        click.echo("\nProcess interrupted. Exiting...")
        sys.exit(1)
    except Exception as err:  # pylint: disable=W0703
        click.echo(err)
        sys.exit(1)
