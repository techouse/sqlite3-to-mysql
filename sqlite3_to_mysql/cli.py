"""The command line interface of SQLite3toMySQL."""

import sys

import click
from tabulate import tabulate

from . import SQLite3toMySQL
from .click_utils import OptionEatAll, prompt_password
from .debug_info import info


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
    "-t",
    "--sqlite-tables",
    cls=OptionEatAll,
    help="Transfer only these specific tables (space separated table names). "
    "Implies --without-foreign-keys which inhibits the transfer of foreign keys.",
)
@click.option(
    "-X", "--without-foreign-keys", is_flag=True, help="Do not transfer foreign keys."
)
@click.option(
    "-d", "--mysql-database", default=None, help="MySQL database name", required=True
)
@click.option("-u", "--mysql-user", default=None, help="MySQL user", required=True)
@click.option(
    "-p",
    "--prompt-mysql-password",
    is_flag=True,
    default=False,
    callback=prompt_password,
    help="Prompt for MySQL password",
)
@click.option("--mysql-password", default=None, help="MySQL password")
@click.option(
    "-h", "--mysql-host", default="localhost", help="MySQL host. Defaults to localhost."
)
@click.option(
    "-P", "--mysql-port", type=int, default=3306, help="MySQL port. Defaults to 3306."
)
@click.option(
    "-S", "--skip-ssl", is_flag=True, help="Disable MySQL connection encryption."
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
    "-T",
    "--use-fulltext",
    is_flag=True,
    help="Use FULLTEXT indexes on TEXT columns. "
    "Will throw an error if your MySQL version does not support InnoDB FULLTEXT indexes!",
)
@click.option("--with-rowid", is_flag=True, help="Transfer rowid columns.")
@click.option(
    "-c", "--chunk", type=int, default=None, help="Chunk reading/writing SQL records"
)
@click.option("-l", "--log-file", type=click.Path(), help="Log file")
@click.option("-q", "--quiet", is_flag=True, help="Quiet. Display only errors.")
@click.version_option(
    message=tabulate(info(), headers=["software", "version"], tablefmt="github")
)
def cli(
    sqlite_file,
    sqlite_tables,
    without_foreign_keys,
    mysql_user,
    prompt_mysql_password,
    mysql_password,
    mysql_database,
    mysql_host,
    mysql_port,
    skip_ssl,
    mysql_integer_type,
    mysql_string_type,
    use_fulltext,
    with_rowid,
    chunk,
    log_file,
    quiet,
):
    """Transfer SQLite to MySQL using the provided CLI options."""
    try:
        converter = SQLite3toMySQL(
            sqlite_file=sqlite_file,
            sqlite_tables=sqlite_tables,
            without_foreign_keys=without_foreign_keys
            or (sqlite_tables is not None and len(sqlite_tables) > 0),
            mysql_user=mysql_user,
            mysql_password=mysql_password or prompt_mysql_password,
            mysql_database=mysql_database,
            mysql_host=mysql_host,
            mysql_port=mysql_port,
            mysql_ssl_disabled=skip_ssl,
            mysql_integer_type=mysql_integer_type,
            mysql_string_type=mysql_string_type,
            use_fulltext=use_fulltext,
            with_rowid=with_rowid,
            chunk=chunk,
            log_file=log_file,
            quiet=quiet,
        )
        converter.transfer()
    except KeyboardInterrupt:
        click.echo("\nProcess interrupted. Exiting...")
        sys.exit(1)
    except Exception as err:  # pylint: disable=W0703
        click.echo(err)
        sys.exit(1)
