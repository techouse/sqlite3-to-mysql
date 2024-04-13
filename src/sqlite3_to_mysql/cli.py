"""The command line interface of SQLite3toMySQL."""

import os
import sys
import typing as t
from datetime import datetime

import click
from mysql.connector import CharacterSet
from tabulate import tabulate

from . import SQLite3toMySQL
from . import __version__ as package_version
from .click_utils import OptionEatAll, prompt_password
from .debug_info import info
from .mysql_utils import MYSQL_INSERT_METHOD, MYSQL_TEXT_COLUMN_TYPES, mysql_supported_character_sets


_copyright_header: str = f"sqlite3mysql version {package_version} Copyright (c) 2018-{datetime.now().year} Klemen Tusar"


@click.command(
    name="sqlite3mysql",
    help=_copyright_header,
    no_args_is_help=True,
    epilog="For more information, visit https://github.com/techouse/sqlite3-to-mysql",
)
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
    type=tuple,
    cls=OptionEatAll,
    help="Transfer only these specific tables (space separated table names). "
    "Implies --without-foreign-keys which inhibits the transfer of foreign keys.",
)
@click.option("-X", "--without-foreign-keys", is_flag=True, help="Do not transfer foreign keys.")
@click.option(
    "-W",
    "--ignore-duplicate-keys",
    is_flag=True,
    help="Ignore duplicate keys. The default behavior is to create new ones with a numerical suffix, e.g. "
    "'exising_key' -> 'existing_key_1'",
)
@click.option("-d", "--mysql-database", default=None, help="MySQL database name", required=True)
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
@click.option("-h", "--mysql-host", default="localhost", help="MySQL host. Defaults to localhost.")
@click.option("-P", "--mysql-port", type=int, default=3306, help="MySQL port. Defaults to 3306.")
@click.option("-S", "--skip-ssl", is_flag=True, help="Disable MySQL connection encryption.")
@click.option(
    "-i",
    "--mysql-insert-method",
    type=click.Choice(MYSQL_INSERT_METHOD, case_sensitive=False),
    default="IGNORE",
    help="MySQL insert method. DEFAULT will throw errors when encountering duplicate records; "
    "UPDATE will update existing rows; IGNORE will ignore insert errors. Defaults to IGNORE.",
)
@click.option(
    "-E",
    "--mysql-truncate-tables",
    is_flag=True,
    help="Truncates existing tables before inserting data.",
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
    "--mysql-text-type",
    type=click.Choice(MYSQL_TEXT_COLUMN_TYPES, case_sensitive=False),
    default="TEXT",
    help="MySQL default text field type. Defaults to TEXT.",
)
@click.option(
    "--mysql-charset",
    metavar="TEXT",
    type=click.Choice(list(CharacterSet().get_supported()), case_sensitive=False),
    default="utf8mb4",
    show_default=True,
    help="MySQL database and table character set",
)
@click.option(
    "--mysql-collation",
    metavar="TEXT",
    type=click.Choice(
        [charset.collation for charset in mysql_supported_character_sets()],
        case_sensitive=False,
    ),
    default=None,
    help="MySQL database and table collation",
)
@click.option(
    "-T",
    "--use-fulltext",
    is_flag=True,
    help="Use FULLTEXT indexes on TEXT columns. "
    "Will throw an error if your MySQL version does not support InnoDB FULLTEXT indexes!",
)
@click.option("--with-rowid", is_flag=True, help="Transfer rowid columns.")
@click.option("-c", "--chunk", type=int, default=None, help="Chunk reading/writing SQL records")
@click.option("-l", "--log-file", type=click.Path(), help="Log file")
@click.option("-q", "--quiet", is_flag=True, help="Quiet. Display only errors.")
@click.option("--debug", is_flag=True, help="Debug mode. Will throw exceptions.")
@click.version_option(message=tabulate(info(), headers=["software", "version"], tablefmt="github"))
def cli(
    sqlite_file: t.Union[str, "os.PathLike[t.Any]"],
    sqlite_tables: t.Optional[t.Sequence[str]],
    without_foreign_keys: bool,
    ignore_duplicate_keys: bool,
    mysql_user: str,
    prompt_mysql_password: bool,
    mysql_password: str,
    mysql_database: str,
    mysql_host: str,
    mysql_port: int,
    skip_ssl: bool,
    mysql_insert_method: str,
    mysql_truncate_tables: bool,
    mysql_integer_type: str,
    mysql_string_type: str,
    mysql_text_type: str,
    mysql_charset: str,
    mysql_collation: str,
    use_fulltext: bool,
    with_rowid: bool,
    chunk: int,
    log_file: t.Union[str, "os.PathLike[t.Any]"],
    quiet: bool,
    debug: bool,
) -> None:
    """Transfer SQLite to MySQL using the provided CLI options."""
    click.echo(_copyright_header)
    try:
        if mysql_collation:
            charset_collations: t.Tuple[str, ...] = tuple(
                cs.collation for cs in mysql_supported_character_sets(mysql_charset.lower())
            )
            if mysql_collation not in set(charset_collations):
                raise click.ClickException(
                    f"""Error: Invalid value for '--collation' of charset '{mysql_charset}': '{mysql_collation}' is not one of {"'" + "', '".join(charset_collations) + "'"}."""
                )

        SQLite3toMySQL(
            sqlite_file=sqlite_file,
            sqlite_tables=sqlite_tables or tuple(),
            without_foreign_keys=without_foreign_keys or (sqlite_tables is not None and len(sqlite_tables) > 0),
            mysql_user=mysql_user,
            mysql_password=mysql_password or prompt_mysql_password,
            mysql_database=mysql_database,
            mysql_host=mysql_host,
            mysql_port=mysql_port,
            mysql_ssl_disabled=skip_ssl,
            mysql_insert_method=mysql_insert_method,
            mysql_truncate_tables=mysql_truncate_tables,
            mysql_integer_type=mysql_integer_type,
            mysql_string_type=mysql_string_type,
            mysql_text_type=mysql_text_type,
            mysql_charset=mysql_charset.lower() if mysql_charset else "utf8mb4",
            mysql_collation=mysql_collation.lower() if mysql_collation else None,
            ignore_duplicate_keys=ignore_duplicate_keys,
            use_fulltext=use_fulltext,
            with_rowid=with_rowid,
            chunk=chunk,
            log_file=log_file,
            quiet=quiet,
        ).transfer()
    except KeyboardInterrupt:
        if debug:
            raise
        click.echo("\nProcess interrupted. Exiting...")
        sys.exit(1)
    except Exception as err:  # pylint: disable=W0703
        if debug:
            raise
        click.echo(err)
        sys.exit(1)
