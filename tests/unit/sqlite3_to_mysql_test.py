import logging
import re
import typing as t
from random import choice

import mysql.connector
import pytest
from _pytest.logging import LogCaptureFixture
from faker import Faker
from mysql.connector import errorcode
from pytest_mock import MockerFixture, MockFixture
from sqlalchemy import Connection, CursorResult, Engine, Inspector, TextClause, create_engine, inspect, text
from sqlalchemy.dialects.sqlite import __all__ as sqlite_column_types

from sqlite3_to_mysql import SQLite3toMySQL
from tests.conftest import MySQLCredentials


@pytest.mark.usefixtures("sqlite_database", "mysql_instance")
class TestSQLite3toMySQL:
    @pytest.mark.parametrize("quiet", [False, True])
    def test_translate_type_from_sqlite_to_mysql_invalid_column_type(
        self,
        sqlite_database: str,
        mysql_database: Engine,
        mysql_credentials: MySQLCredentials,
        mocker: MockerFixture,
        quiet: bool,
    ) -> None:
        proc: SQLite3toMySQL = SQLite3toMySQL(  # type: ignore[call-arg]
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            quiet=quiet,
        )
        with pytest.raises(ValueError) as excinfo:
            mocker.patch.object(proc, "_valid_column_type", return_value=False)
            proc._translate_type_from_sqlite_to_mysql("text")
        assert "is not a valid column_type!" in str(excinfo.value)

    @pytest.mark.parametrize(
        "mysql_integer_type, mysql_string_type, mysql_text_type",
        [
            ("INT(11)", "VARCHAR(300)", "TEXT"),
            ("BIGINT(19)", "TEXT", "MEDIUMTEXT"),
            ("BIGINT(19)", "MEDIUMTEXT", "TINYTEXT"),
            ("BIGINT(20) UNSIGNED", "CHAR(100)", "LONGTEXT"),
        ],
    )
    def test_translate_type_from_sqlite_to_mysql_all_valid_columns(
        self,
        sqlite_database: str,
        mysql_database: Engine,
        mysql_credentials: MySQLCredentials,
        faker: Faker,
        mysql_integer_type: str,
        mysql_string_type: str,
        mysql_text_type: str,
    ) -> None:
        proc: SQLite3toMySQL = SQLite3toMySQL(  # type: ignore
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            mysql_integer_type=mysql_integer_type,
            mysql_string_type=mysql_string_type,
            mysql_text_type=mysql_text_type,
        )

        for column in sqlite_column_types + ("INT64",):
            if column in {"Insert", "insert", "dialect"}:
                continue
            elif column == "VARCHAR":
                assert proc._translate_type_from_sqlite_to_mysql(column) == proc._mysql_string_type
            elif column in {"INTEGER", "INT"}:
                assert proc._translate_type_from_sqlite_to_mysql(column) == proc._mysql_integer_type
            elif column in {"INT64", "NUMERIC"}:
                assert proc._translate_type_from_sqlite_to_mysql(column) == "BIGINT(19)"
            elif column in {"TINYTEXT", "TEXT", "MEDIUMTEXT", "LONGTEXT"}:
                assert proc._translate_type_from_sqlite_to_mysql(column) == proc._mysql_text_type
            elif column == "BOOLEAN":
                assert proc._translate_type_from_sqlite_to_mysql(column) == "TINYINT(1)"
            else:
                assert proc._translate_type_from_sqlite_to_mysql(column) == column
        assert proc._translate_type_from_sqlite_to_mysql("TEXT") == proc._mysql_text_type
        assert proc._translate_type_from_sqlite_to_mysql("CLOB") == proc._mysql_text_type
        assert proc._translate_type_from_sqlite_to_mysql("CHARACTER") == "CHAR"
        length: int = faker.pyint(min_value=1, max_value=99)
        assert proc._translate_type_from_sqlite_to_mysql(f"CHARACTER({length})") == f"CHAR({length})"
        assert proc._translate_type_from_sqlite_to_mysql("NCHAR") == "CHAR"
        length = faker.pyint(min_value=1, max_value=99)
        assert proc._translate_type_from_sqlite_to_mysql(f"NCHAR({length})") == f"CHAR({length})"
        assert proc._translate_type_from_sqlite_to_mysql("NATIVE CHARACTER") == "CHAR"
        length = faker.pyint(min_value=1, max_value=99)
        assert proc._translate_type_from_sqlite_to_mysql(f"NATIVE CHARACTER({length})") == f"CHAR({length})"
        assert proc._translate_type_from_sqlite_to_mysql("VARCHAR") == proc._mysql_string_type
        length = faker.pyint(min_value=1, max_value=255)
        assert proc._translate_type_from_sqlite_to_mysql(f"VARCHAR({length})") == re.sub(
            r"\d+", str(length), proc._mysql_string_type
        )
        assert proc._translate_type_from_sqlite_to_mysql("DOUBLE PRECISION") == "DOUBLE"
        assert proc._translate_type_from_sqlite_to_mysql("UNSIGNED BIG INT") == "BIGINT UNSIGNED"
        length = faker.pyint(min_value=1000000000, max_value=99999999999999999999)
        assert proc._translate_type_from_sqlite_to_mysql(f"UNSIGNED BIG INT({length})") == f"BIGINT({length}) UNSIGNED"
        assert proc._translate_type_from_sqlite_to_mysql("INT1") == proc._mysql_integer_type
        assert proc._translate_type_from_sqlite_to_mysql("INT2") == proc._mysql_integer_type
        length = faker.pyint(min_value=1, max_value=11)
        assert proc._translate_type_from_sqlite_to_mysql(f"INT({length})") == re.sub(
            r"\d+", str(length), proc._mysql_integer_type
        )
        for column in {"META", "FOO", "BAR"}:
            assert proc._translate_type_from_sqlite_to_mysql(column) == proc._mysql_string_type
        precision: int = faker.pyint(min_value=3, max_value=19)
        scale: int = faker.pyint(min_value=0, max_value=precision - 1)
        assert (
            proc._translate_type_from_sqlite_to_mysql(f"DECIMAL({precision},{scale})")
            == f"DECIMAL({precision},{scale})"
        )

    @pytest.mark.parametrize("quiet", [False, True])
    def test_create_database_connection_error(
        self,
        sqlite_database: str,
        mysql_database: Engine,
        mysql_credentials: MySQLCredentials,
        mocker: MockerFixture,
        faker: Faker,
        caplog: LogCaptureFixture,
        quiet: bool,
    ) -> None:
        proc: SQLite3toMySQL = SQLite3toMySQL(  # type: ignore[call-arg]
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            quiet=quiet,
        )

        class FakeCursor:
            def execute(self, statement: t.Any) -> None:
                raise mysql.connector.Error(msg="Unknown MySQL error", errno=errorcode.CR_UNKNOWN_ERROR)

        mocker.patch.object(proc, "_mysql_cur", FakeCursor())

        with pytest.raises(mysql.connector.Error) as excinfo:
            caplog.set_level(logging.DEBUG)
            proc._create_database()
        assert str(errorcode.CR_UNKNOWN_ERROR) in str(excinfo.value)
        assert any(str(errorcode.CR_UNKNOWN_ERROR) in message for message in caplog.messages)

    @pytest.mark.parametrize("quiet", [False, True])
    def test_create_table_cursor_error(
        self,
        sqlite_database: str,
        mysql_database: Engine,
        mysql_credentials: MySQLCredentials,
        mocker: MockerFixture,
        faker: Faker,
        caplog: LogCaptureFixture,
        quiet: bool,
    ) -> None:
        proc = SQLite3toMySQL(  # type: ignore[call-arg]
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            quiet=quiet,
        )

        class FakeCursor:
            def execute(self, statement):
                raise mysql.connector.Error(msg="Unknown MySQL error", errno=errorcode.CR_UNKNOWN_ERROR)

        mocker.patch.object(proc, "_mysql_cur", FakeCursor())

        sqlite_engine: Engine = create_engine(f"sqlite:///{sqlite_database}")
        sqlite_inspect: Inspector = inspect(sqlite_engine)
        sqlite_tables: t.List[str] = sqlite_inspect.get_table_names()

        with pytest.raises(mysql.connector.Error) as excinfo:
            caplog.set_level(logging.DEBUG)
            proc._create_table(choice(sqlite_tables))
        assert str(errorcode.CR_UNKNOWN_ERROR) in str(excinfo.value)
        assert any(str(errorcode.CR_UNKNOWN_ERROR) in message for message in caplog.messages)

        sqlite_engine.dispose()

    @pytest.mark.parametrize("quiet", [False, True])
    def test_process_cursor_error(
        self,
        sqlite_database: str,
        mysql_database: Engine,
        mysql_credentials: MySQLCredentials,
        mocker: MockerFixture,
        faker: Faker,
        caplog: LogCaptureFixture,
        quiet: bool,
    ) -> None:
        proc = SQLite3toMySQL(  # type: ignore[call-arg]
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            quiet=quiet,
        )

        def fake_transfer_table_data(sql, total_records=0):
            raise mysql.connector.Error(msg="Unknown MySQL error", errno=errorcode.CR_UNKNOWN_ERROR)

        mocker.patch.object(proc, "_transfer_table_data", fake_transfer_table_data)

        with pytest.raises(mysql.connector.Error) as excinfo:
            caplog.set_level(logging.DEBUG)
            proc.transfer()
        assert str(errorcode.CR_UNKNOWN_ERROR) in str(excinfo.value)
        assert any(str(errorcode.CR_UNKNOWN_ERROR) in message for message in caplog.messages)

    @pytest.mark.parametrize("quiet", [False, True])
    def test_add_indices_error(
        self,
        sqlite_database: str,
        mysql_database: Engine,
        mysql_credentials: MySQLCredentials,
        mocker: MockerFixture,
        faker: Faker,
        caplog: LogCaptureFixture,
        quiet: bool,
    ) -> None:
        proc = SQLite3toMySQL(  # type: ignore[call-arg]
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            quiet=quiet,
        )

        sqlite_engine: Engine = create_engine(f"sqlite:///{sqlite_database}")
        sqlite_inspect: Inspector = inspect(sqlite_engine)
        sqlite_tables: t.List[str] = sqlite_inspect.get_table_names()

        tables_with_indices: t.List[str] = []
        for table in sqlite_tables:
            if sqlite_inspect.get_indexes(table):
                tables_with_indices.append(table)

        table_name: str = choice(tables_with_indices)
        proc._create_table(table_name)

        class FakeCursor:
            def execute(self, statement):
                raise mysql.connector.Error(msg="Unknown MySQL error", errno=errorcode.CR_UNKNOWN_ERROR)

        mocker.patch.object(proc, "_mysql_cur", FakeCursor())

        with pytest.raises(mysql.connector.Error) as excinfo:
            caplog.set_level(logging.DEBUG)
            proc._add_indices(table_name)
        assert str(errorcode.CR_UNKNOWN_ERROR) in str(excinfo.value)
        assert any(str(errorcode.CR_UNKNOWN_ERROR) in message for message in caplog.messages)

        sqlite_engine.dispose()

    @pytest.mark.parametrize("quiet", [False, True])
    def test_add_foreign_keys_error(
        self,
        sqlite_database: str,
        mysql_database: Engine,
        mysql_credentials: MySQLCredentials,
        mocker: MockFixture,
        faker: Faker,
        caplog: LogCaptureFixture,
        quiet: bool,
    ) -> None:
        proc = SQLite3toMySQL(  # type: ignore[call-arg]
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            quiet=quiet,
        )

        sqlite_engine: Engine = create_engine(f"sqlite:///{sqlite_database}")
        sqlite_inspect: Inspector = inspect(sqlite_engine)
        sqlite_cnx: Connection = sqlite_engine.connect()
        sqlite_tables: t.List[str] = sqlite_inspect.get_table_names()

        tables_with_foreign_keys: t.List[str] = []

        for table in sqlite_tables:
            sqlite_fk_stmt: TextClause = text(f'PRAGMA foreign_key_list("{table}")')
            sqlite_fk_result: CursorResult[t.Any] = sqlite_cnx.execute(sqlite_fk_stmt)
            if sqlite_fk_result.returns_rows:
                for _ in sqlite_fk_result:
                    tables_with_foreign_keys.append(table)
                    break

        table_name: str = choice(tables_with_foreign_keys)

        proc._create_table(table_name)

        class FakeCursor:
            def execute(self, statement):
                raise mysql.connector.Error(msg="Unknown MySQL error", errno=errorcode.CR_UNKNOWN_ERROR)

        mocker.patch.object(proc, "_mysql_cur", FakeCursor())

        with pytest.raises(mysql.connector.Error) as excinfo:
            caplog.set_level(logging.DEBUG)
            proc._add_foreign_keys(table_name)
        assert str(errorcode.CR_UNKNOWN_ERROR) in str(excinfo.value)
        assert any(str(errorcode.CR_UNKNOWN_ERROR) in message for message in caplog.messages)

        sqlite_cnx.close()
        sqlite_engine.dispose()
