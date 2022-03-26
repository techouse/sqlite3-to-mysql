from random import choice, sample

import pytest
import simplejson as json
import six
from sqlalchemy import create_engine, inspect

from sqlite3_to_mysql import SQLite3toMySQL
from sqlite3_to_mysql.cli import cli as sqlite3mysql
from sqlite3_to_mysql.mysql_utils import MYSQL_INSERT_METHOD


@pytest.mark.cli
@pytest.mark.usefixtures("sqlite_database", "mysql_instance")
class TestSQLite3toMySQL:
    def test_no_arguments(self, cli_runner, mysql_database):
        result = cli_runner.invoke(sqlite3mysql)
        assert result.exit_code > 0
        assert any(
            message in result.output
            for message in {
                'Error: Missing option "-f" / "--sqlite-file"',
                "Error: Missing option '-f' / '--sqlite-file'",
            }
        )

    def test_non_existing_sqlite_file(self, cli_runner, mysql_database, faker):
        result = cli_runner.invoke(
            sqlite3mysql, ["-f", faker.file_path(depth=1, extension=".sqlite3")]
        )
        assert result.exit_code > 0
        assert "Error: Invalid value" in result.output
        assert "does not exist" in result.output

    def test_no_database_name(self, cli_runner, sqlite_database, mysql_database):
        result = cli_runner.invoke(sqlite3mysql, ["-f", sqlite_database])
        assert result.exit_code > 0
        assert any(
            message in result.output
            for message in {
                'Error: Missing option "-d" / "--mysql-database"',
                "Error: Missing option '-d' / '--mysql-database'",
            }
        )

    def test_no_database_user(
        self, cli_runner, sqlite_database, mysql_credentials, mysql_database
    ):
        result = cli_runner.invoke(
            sqlite3mysql, ["-f", sqlite_database, "-d", mysql_credentials.database]
        )
        assert result.exit_code > 0
        assert any(
            message in result.output
            for message in {
                'Error: Missing option "-u" / "--mysql-user"',
                "Error: Missing option '-u' / '--mysql-user'",
            }
        )

    def test_invalid_database_name(
        self, cli_runner, sqlite_database, mysql_credentials, mysql_database, faker
    ):
        result = cli_runner.invoke(
            sqlite3mysql,
            [
                "-f",
                sqlite_database,
                "-d",
                "_".join(faker.words(nb=3)),
                "-u",
                faker.first_name().lower(),
            ],
        )
        assert result.exit_code > 0
        assert "1045 (28000): Access denied" in result.output

    def test_invalid_database_user(
        self, cli_runner, sqlite_database, mysql_credentials, mysql_database, faker
    ):
        result = cli_runner.invoke(
            sqlite3mysql,
            [
                "-f",
                sqlite_database,
                "-d",
                mysql_credentials.database,
                "-u",
                faker.first_name().lower(),
            ],
        )
        assert result.exit_code > 0
        assert "1045 (28000): Access denied" in result.output

    def test_invalid_database_password(
        self, cli_runner, sqlite_database, mysql_credentials, mysql_database, faker
    ):
        result = cli_runner.invoke(
            sqlite3mysql,
            [
                "-f",
                sqlite_database,
                "-d",
                mysql_credentials.database,
                "-u",
                mysql_credentials.user,
                "--mysql-password",
                faker.password(length=16),
            ],
        )
        assert result.exit_code > 0
        assert "1045 (28000): Access denied" in result.output

    def test_database_password_prompt(
        self,
        cli_runner,
        sqlite_database,
        mysql_credentials,
        mysql_database,
    ):
        result = cli_runner.invoke(
            sqlite3mysql,
            args=[
                "-f",
                sqlite_database,
                "-d",
                mysql_credentials.database,
                "-u",
                mysql_credentials.user,
                "-p",
            ],
            input=mysql_credentials.password,
        )
        assert result.exit_code == 0

    def test_invalid_database_password_prompt(
        self,
        cli_runner,
        sqlite_database,
        mysql_credentials,
        mysql_database,
        faker,
    ):
        result = cli_runner.invoke(
            sqlite3mysql,
            args=[
                "-f",
                sqlite_database,
                "-d",
                mysql_credentials.database,
                "-u",
                mysql_credentials.user,
                "-p",
            ],
            input=faker.password(length=16),
        )
        assert result.exit_code > 0
        assert "1045 (28000): Access denied" in result.output

    def test_invalid_database_port(
        self, cli_runner, sqlite_database, mysql_credentials, mysql_database, faker
    ):
        if six.PY2:
            port = choice(xrange(2, 2**16 - 1))
        else:
            port = choice(range(2, 2**16 - 1))
        if port == mysql_credentials.port:
            port -= 1
        result = cli_runner.invoke(
            sqlite3mysql,
            [
                "-f",
                sqlite_database,
                "-d",
                mysql_credentials.database,
                "-u",
                mysql_credentials.user,
                "--mysql-password",
                mysql_credentials.password,
                "-h",
                mysql_credentials.host,
                "-P",
                port,
            ],
        )
        assert result.exit_code > 0
        assert any(
            message in result.output
            for message in {
                "2003 (HY000): Can't connect to MySQL server on",
                "2003: Can't connect to MySQL server",
            }
        )

    @pytest.mark.parametrize(
        "mysql_integer_type,"
        "mysql_string_type,"
        "mysql_text_type,"
        "chunk,"
        "with_rowid,"
        "mysql_insert_method,"
        "ignore_duplicate_keys",
        [
            # 00000
            (None, None, None, None, False, "DEFAULT", False),
            # 10000
            ("BIGINT(19)", None, None, None, False, "UPDATE", True),
            # 01000
            (None, "VARCHAR(512)", None, None, False, "IGNORE", False),
            # 11000
            ("BIGINT(19)", "VARCHAR(512)", None, None, False, "DEFAULT", True),
            # 00100
            (None, None, "MEDIUMTEXT", None, False, "UPDATE", False),
            # 10100
            ("BIGINT(19)", None, "MEDIUMTEXT", None, False, "IGNORE", True),
            # 01100
            (None, "VARCHAR(512)", "MEDIUMTEXT", None, False, "DEFAULT", False),
            # 11100
            ("BIGINT(19)", "VARCHAR(512)", "MEDIUMTEXT", None, False, "UPDATE", True),
            # 00010
            (None, None, None, 10, False, "IGNORE", False),
            # 10010
            ("BIGINT(19)", None, None, 10, False, "DEFAULT", True),
            # 01010
            (None, "VARCHAR(512)", None, 10, False, "UPDATE", False),
            # 11010
            ("BIGINT(19)", "VARCHAR(512)", None, 10, False, "IGNORE", True),
            # 00110
            (None, None, "MEDIUMTEXT", 10, False, "DEFAULT", False),
            # 10110
            ("BIGINT(19)", None, "MEDIUMTEXT", 10, False, "UPDATE", True),
            # 01110
            (None, "VARCHAR(512)", "MEDIUMTEXT", 10, False, "IGNORE", False),
            # 11110
            ("BIGINT(19)", "VARCHAR(512)", "MEDIUMTEXT", 10, False, "DEFAULT", True),
            # 00001
            (None, None, None, None, True, "UPDATE", False),
            # 10001
            ("BIGINT(19)", None, None, None, True, "IGNORE", True),
            # 01001
            (None, "VARCHAR(512)", None, None, True, "DEFAULT", False),
            # 11001
            ("BIGINT(19)", "VARCHAR(512)", None, None, True, "UPDATE", True),
            # 00101
            (None, None, "MEDIUMTEXT", None, True, "IGNORE", False),
            # 10101
            ("BIGINT(19)", None, "MEDIUMTEXT", None, True, "DEFAULT", True),
            # 01101
            (None, "VARCHAR(512)", "MEDIUMTEXT", None, True, "UPDATE", False),
            # 11101
            ("BIGINT(19)", "VARCHAR(512)", "MEDIUMTEXT", None, True, "IGNORE", True),
            # 00011
            (None, None, None, 10, True, "DEFAULT", False),
            # 10011
            ("BIGINT(19)", None, None, 10, True, "UPDATE", True),
            # 01011
            (None, "VARCHAR(512)", None, 10, True, "IGNORE", False),
            # 11011
            ("BIGINT(19)", "VARCHAR(512)", None, 10, True, "DEFAULT", True),
            # 00111
            (None, None, "MEDIUMTEXT", 10, True, "UPDATE", False),
            # 10111
            ("BIGINT(19)", None, "MEDIUMTEXT", 10, True, "IGNORE", True),
            # 01111
            (None, "VARCHAR(512)", "MEDIUMTEXT", 10, True, "DEFAULT", False),
            # 11111
            ("BIGINT(19)", "VARCHAR(512)", "MEDIUMTEXT", 10, True, "UPDATE", True),
        ],
    )
    def test_minimum_valid_parameters(
        self,
        cli_runner,
        sqlite_database,
        mysql_credentials,
        mysql_integer_type,
        mysql_string_type,
        mysql_text_type,
        mysql_database,
        chunk,
        with_rowid,
        mysql_insert_method,
        ignore_duplicate_keys,
    ):
        arguments = [
            "-f",
            sqlite_database,
            "-d",
            mysql_credentials.database,
            "-u",
            mysql_credentials.user,
            "--mysql-password",
            mysql_credentials.password,
            "-h",
            mysql_credentials.host,
            "-P",
            mysql_credentials.port,
            "--mysql-insert-method",
            mysql_insert_method,
        ]
        if mysql_integer_type:
            arguments.append("--mysql-integer-type")
            arguments.append(mysql_integer_type)
        if mysql_string_type:
            arguments.append("--mysql-string-type")
            arguments.append(mysql_string_type)
        if mysql_text_type:
            arguments.append("--mysql-text-type")
            arguments.append(mysql_text_type)
        if chunk:
            arguments.append("-c")
            arguments.append(chunk)
        if with_rowid:
            arguments.append("--with-rowid")
        if ignore_duplicate_keys:
            arguments.append("--ignore-duplicate-keys")
        result = cli_runner.invoke(
            sqlite3mysql,
            arguments,
        )
        assert result.exit_code == 0

    def test_keyboard_interrupt(
        self, cli_runner, sqlite_database, mysql_credentials, mocker
    ):
        mocker.patch.object(SQLite3toMySQL, "transfer", side_effect=KeyboardInterrupt())
        result = cli_runner.invoke(
            sqlite3mysql,
            [
                "-f",
                sqlite_database,
                "-d",
                mysql_credentials.database,
                "-u",
                mysql_credentials.user,
                "--mysql-password",
                mysql_credentials.password,
                "-h",
                mysql_credentials.host,
                "-P",
                mysql_credentials.port,
            ],
        )
        assert result.exit_code > 0
        assert "Process interrupted" in result.output

    def test_transfer_specific_tables_only(
        self, cli_runner, sqlite_database, mysql_credentials
    ):
        sqlite_engine = create_engine(
            "sqlite:///{database}".format(database=sqlite_database),
            json_serializer=json.dumps,
            json_deserializer=json.loads,
        )
        sqlite_inspect = inspect(sqlite_engine)
        sqlite_tables = sqlite_inspect.get_table_names()

        if six.PY2:
            table_number = choice(xrange(1, len(sqlite_tables)))
        else:
            table_number = choice(range(1, len(sqlite_tables)))

        result = cli_runner.invoke(
            sqlite3mysql,
            [
                "-f",
                sqlite_database,
                "-t",
                " ".join(sample(sqlite_tables, table_number)),
                "-d",
                mysql_credentials.database,
                "-u",
                mysql_credentials.user,
                "--mysql-password",
                mysql_credentials.password,
                "-h",
                mysql_credentials.host,
                "-P",
                mysql_credentials.port,
            ],
        )
        assert result.exit_code == 0

    def test_version(self, cli_runner):
        result = cli_runner.invoke(sqlite3mysql, ["--version"])
        assert result.exit_code == 0
        assert all(
            message in result.output
            for message in {
                "sqlite3-to-mysql",
                "Operating",
                "System",
                "Python",
                "MySQL",
                "SQLite",
                "click",
                "mysql-connector-python",
                "pytimeparse",
                "simplejson",
                "six",
                "tabulate",
                "tqdm",
            }
        )

    @pytest.mark.xfail
    @pytest.mark.parametrize(
        "mysql_integer_type, mysql_string_type, mysql_text_type, chunk, with_rowid",
        [
            # 00000
            (None, None, None, None, False),
            # 10000
            ("BIGINT(19)", None, None, None, False),
            # 01000
            (None, "VARCHAR(512)", None, None, False),
            # 11000
            ("BIGINT(19)", "VARCHAR(512)", None, None, False),
            # 00100
            (None, None, "MEDIUMTEXT", None, False),
            # 10100
            ("BIGINT(19)", None, "MEDIUMTEXT", None, False),
            # 01100
            (None, "VARCHAR(512)", "MEDIUMTEXT", None, False),
            # 11100
            ("BIGINT(19)", "VARCHAR(512)", "MEDIUMTEXT", None, False),
            # 00010
            (None, None, None, 10, False),
            # 10010
            ("BIGINT(19)", None, None, 10, False),
            # 01010
            (None, "VARCHAR(512)", None, 10, False),
            # 11010
            ("BIGINT(19)", "VARCHAR(512)", None, 10, False),
            # 00110
            (None, None, "MEDIUMTEXT", 10, False),
            # 10110
            ("BIGINT(19)", None, "MEDIUMTEXT", 10, False),
            # 01110
            (None, "VARCHAR(512)", "MEDIUMTEXT", 10, False),
            # 11110
            ("BIGINT(19)", "VARCHAR(512)", "MEDIUMTEXT", 10, False),
            # 00001
            (None, None, None, None, True),
            # 10001
            ("BIGINT(19)", None, None, None, True),
            # 01001
            (None, "VARCHAR(512)", None, None, True),
            # 11001
            ("BIGINT(19)", "VARCHAR(512)", None, None, True),
            # 00101
            (None, None, "MEDIUMTEXT", None, True),
            # 10101
            ("BIGINT(19)", None, "MEDIUMTEXT", None, True),
            # 01101
            (None, "VARCHAR(512)", "MEDIUMTEXT", None, True),
            # 11101
            ("BIGINT(19)", "VARCHAR(512)", "MEDIUMTEXT", None, True),
            # 00011
            (None, None, None, 10, True),
            # 10011
            ("BIGINT(19)", None, None, 10, True),
            # 01011
            (None, "VARCHAR(512)", None, 10, True),
            # 11011
            ("BIGINT(19)", "VARCHAR(512)", None, 10, True),
            # 00111
            (None, None, "MEDIUMTEXT", 10, True),
            # 10111
            ("BIGINT(19)", None, "MEDIUMTEXT", 10, True),
            # 01111
            (None, "VARCHAR(512)", "MEDIUMTEXT", 10, True),
            # 11111
            ("BIGINT(19)", "VARCHAR(512)", "MEDIUMTEXT", 10, True),
        ],
    )
    def test_quiet(
        self,
        cli_runner,
        mysql_database,
        sqlite_database,
        mysql_credentials,
        mysql_integer_type,
        mysql_string_type,
        mysql_text_type,
        chunk,
        with_rowid,
    ):
        arguments = [
            "-f",
            sqlite_database,
            "-d",
            mysql_credentials.database,
            "-u",
            mysql_credentials.user,
            "--mysql-password",
            mysql_credentials.password,
            "-h",
            mysql_credentials.host,
            "-P",
            mysql_credentials.port,
            "-q",
        ]
        if mysql_integer_type:
            arguments.append("--mysql-integer-type")
            arguments.append(mysql_integer_type)
        if mysql_string_type:
            arguments.append("--mysql-string-type")
            arguments.append(mysql_string_type)
        if mysql_text_type:
            arguments.append("--mysql-text-type")
            arguments.append(mysql_text_type)
        if chunk:
            arguments.append("-c")
            arguments.append(chunk)
        if with_rowid:
            arguments.append("--with-rowid")
        result = cli_runner.invoke(
            sqlite3mysql,
            arguments,
        )
        assert result.exit_code == 0
        assert result.output == ""
