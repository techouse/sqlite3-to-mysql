from random import choice

import pytest
import six

from sqlite3_to_mysql import SQLite3toMySQL
from sqlite3_to_mysql.cli import cli as sqlite3mysql


@pytest.mark.cli
@pytest.mark.usefixtures("sqlite_database", "mysql_instance")
class TestSQLite3toMySQL:
    def test_no_arguments(self, cli_runner, mysql_database):
        result = cli_runner.invoke(sqlite3mysql)
        assert result.exit_code > 0
        assert 'Error: Missing option "-f" / "--sqlite-file"' in result.output

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
        assert 'Error: Missing option "-d" / "--mysql-database"' in result.output

    def test_no_database_user(
        self, cli_runner, sqlite_database, mysql_credentials, mysql_database
    ):
        result = cli_runner.invoke(
            sqlite3mysql, ["-f", sqlite_database, "-d", mysql_credentials.database]
        )
        assert result.exit_code > 0
        assert 'Error: Missing option "-u" / "--mysql-user"' in result.output

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
                "-p",
                faker.password(length=16),
            ],
        )
        assert result.exit_code > 0
        assert "1045 (28000): Access denied" in result.output

    def test_invalid_database_port(
        self, cli_runner, sqlite_database, mysql_credentials, mysql_database, faker
    ):
        if six.PY2:
            port = choice(xrange(2, 2 ** 16 - 1))
        else:
            port = choice(range(2, 2 ** 16 - 1))
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
                "-p",
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
        "mysql_integer_type, mysql_string_type, chunk",
        [
            # 000
            (None, None, None),
            # 111
            ("BIGINT(19)", "TEXT", 10),
            # 110
            ("BIGINT(19)", "TEXT", None),
            # 011
            (None, "TEXT", 10),
            # 010
            (None, "TEXT", None),
            # 100
            ("BIGINT(19)", None, None),
            # 001
            (None, None, 10),
            # 101
            ("BIGINT(19)", None, 10),
        ],
    )
    def test_minimum_valid_parameters(
        self,
        cli_runner,
        sqlite_database,
        mysql_credentials,
        mysql_integer_type,
        mysql_string_type,
        mysql_database,
        chunk,
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
                "-p",
                mysql_credentials.password,
                "-h",
                mysql_credentials.host,
                "-P",
                mysql_credentials.port,
                "--mysql-integer-type",
                mysql_integer_type,
                "--mysql-string-type",
                mysql_string_type,
                "-c",
                chunk,
            ],
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
                "-p",
                mysql_credentials.password,
                "-h",
                mysql_credentials.host,
                "-P",
                mysql_credentials.port,
            ],
        )
        assert result.exit_code > 0
        assert "Process interrupted" in result.output
