import logging
import re
from random import choice

import mysql.connector
import pytest
from mysql.connector import errorcode
from sqlalchemy import create_engine, inspect
from sqlalchemy.dialects.sqlite import __all__ as sqlite_column_types

from sqlite3_to_mysql import SQLite3toMySQL


@pytest.mark.usefixtures("sqlite_database", "mysql_instance")
class TestSQLite3toMySQL:
    @pytest.mark.parametrize("quiet", [False, True])
    def test_translate_type_from_sqlite_to_mysql_invalid_column_type(
        self, sqlite_database, mysql_database, mysql_credentials, mocker, quiet
    ):
        proc = SQLite3toMySQL(
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
        assert "Invalid column_type!" in str(excinfo.value)

    @pytest.mark.parametrize(
        "mysql_integer_type, mysql_string_type",
        [
            ("INT(11)", "VARCHAR(300)"),
            ("BIGINT(19)", "TEXT"),
            ("BIGINT(20) UNSIGNED", "CHAR(100)"),
        ],
    )
    def test_translate_type_from_sqlite_to_mysql_all_valid_columns(
        self,
        sqlite_database,
        mysql_database,
        mysql_credentials,
        faker,
        mysql_integer_type,
        mysql_string_type,
    ):
        proc = SQLite3toMySQL(
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            mysql_integer_type=mysql_integer_type,
            mysql_string_type=mysql_string_type,
        )

        for column in sqlite_column_types + ("INT64",):
            if column == "dialect":
                continue
            elif column == "VARCHAR":
                assert (
                    proc._translate_type_from_sqlite_to_mysql(column)
                    == proc._mysql_string_type
                )
            elif column in {"INTEGER", "INT"}:
                assert (
                    proc._translate_type_from_sqlite_to_mysql(column)
                    == proc._mysql_integer_type
                )
            elif column in {"INT64", "NUMERIC"}:
                assert proc._translate_type_from_sqlite_to_mysql(column) == "BIGINT(19)"
            else:
                assert proc._translate_type_from_sqlite_to_mysql(column) == column
        assert proc._translate_type_from_sqlite_to_mysql("TEXT") == "TEXT"
        assert proc._translate_type_from_sqlite_to_mysql("CLOB") == "TEXT"
        assert proc._translate_type_from_sqlite_to_mysql("CHARACTER") == "CHAR"
        length = faker.pyint(min_value=1, max_value=99)
        assert proc._translate_type_from_sqlite_to_mysql(
            "CHARACTER({})".format(length)
        ) == "CHAR({})".format(length)
        assert proc._translate_type_from_sqlite_to_mysql("NCHAR") == "CHAR"
        length = faker.pyint(min_value=1, max_value=99)
        assert proc._translate_type_from_sqlite_to_mysql(
            "NCHAR({})".format(length)
        ) == "CHAR({})".format(length)
        assert proc._translate_type_from_sqlite_to_mysql("NATIVE CHARACTER") == "CHAR"
        length = faker.pyint(min_value=1, max_value=99)
        assert proc._translate_type_from_sqlite_to_mysql(
            "NATIVE CHARACTER({})".format(length)
        ) == "CHAR({})".format(length)
        assert (
            proc._translate_type_from_sqlite_to_mysql("VARCHAR")
            == proc._mysql_string_type
        )
        length = faker.pyint(min_value=1, max_value=255)
        assert proc._translate_type_from_sqlite_to_mysql(
            "VARCHAR({})".format(length)
        ) == re.sub(r"\d+", str(length), proc._mysql_string_type)
        assert proc._translate_type_from_sqlite_to_mysql("DOUBLE PRECISION") == "DOUBLE"
        assert (
            proc._translate_type_from_sqlite_to_mysql("UNSIGNED BIG INT")
            == "BIGINT UNSIGNED"
        )
        length = faker.pyint(min_value=1000000000, max_value=99999999999999999999)
        assert proc._translate_type_from_sqlite_to_mysql(
            "UNSIGNED BIG INT({})".format(length)
        ) == "BIGINT({}) UNSIGNED".format(length)
        assert (
            proc._translate_type_from_sqlite_to_mysql("INT1")
            == proc._mysql_integer_type
        )
        assert (
            proc._translate_type_from_sqlite_to_mysql("INT2")
            == proc._mysql_integer_type
        )
        length = faker.pyint(min_value=1, max_value=11)
        assert proc._translate_type_from_sqlite_to_mysql(
            "INT({})".format(length)
        ) == re.sub(r"\d+", str(length), proc._mysql_integer_type)
        for column in {"META", "FOO", "BAR"}:
            assert (
                proc._translate_type_from_sqlite_to_mysql(column)
                == proc._mysql_string_type
            )

    @pytest.mark.parametrize("quiet", [False, True])
    def test_create_database_connection_error(
        self,
        sqlite_database,
        mysql_database,
        mysql_credentials,
        mocker,
        faker,
        caplog,
        quiet,
    ):
        proc = SQLite3toMySQL(
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
                raise mysql.connector.Error(
                    msg="Unknown MySQL error", errno=errorcode.CR_UNKNOWN_ERROR
                )

        mocker.patch.object(proc, "_mysql_cur", FakeCursor())

        with pytest.raises(mysql.connector.Error) as excinfo:
            caplog.set_level(logging.DEBUG)
            proc._create_database()
        assert str(errorcode.CR_UNKNOWN_ERROR) in str(excinfo.value)
        assert any(
            str(errorcode.CR_UNKNOWN_ERROR) in message for message in caplog.messages
        )

    @pytest.mark.parametrize("quiet", [False, True])
    def test_create_table_cursor_error(
        self,
        sqlite_database,
        mysql_database,
        mysql_credentials,
        mocker,
        faker,
        caplog,
        quiet,
    ):
        proc = SQLite3toMySQL(
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
                raise mysql.connector.Error(
                    msg="Unknown MySQL error", errno=errorcode.CR_UNKNOWN_ERROR
                )

        mocker.patch.object(proc, "_mysql_cur", FakeCursor())

        sqlite_engine = create_engine(
            "sqlite:///{database}".format(database=sqlite_database)
        )
        sqlite_inspect = inspect(sqlite_engine)
        sqlite_tables = sqlite_inspect.get_table_names()

        with pytest.raises(mysql.connector.Error) as excinfo:
            caplog.set_level(logging.DEBUG)
            proc._create_table(choice(sqlite_tables))
        assert str(errorcode.CR_UNKNOWN_ERROR) in str(excinfo.value)
        assert any(
            str(errorcode.CR_UNKNOWN_ERROR) in message for message in caplog.messages
        )

    @pytest.mark.parametrize("quiet", [False, True])
    def test_process_cursor_error(
        self,
        sqlite_database,
        mysql_database,
        mysql_credentials,
        mocker,
        faker,
        caplog,
        quiet,
    ):
        proc = SQLite3toMySQL(
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            quiet=quiet,
        )

        def fake_transfer_table_data(sql, total_records=0):
            raise mysql.connector.Error(
                msg="Unknown MySQL error", errno=errorcode.CR_UNKNOWN_ERROR
            )

        mocker.patch.object(proc, "_transfer_table_data", fake_transfer_table_data)

        with pytest.raises(mysql.connector.Error) as excinfo:
            caplog.set_level(logging.DEBUG)
            proc.transfer()
        assert str(errorcode.CR_UNKNOWN_ERROR) in str(excinfo.value)
        assert any(
            str(errorcode.CR_UNKNOWN_ERROR) in message for message in caplog.messages
        )

    @pytest.mark.parametrize("quiet", [False, True])
    def test_add_indices_error(
        self,
        sqlite_database,
        mysql_database,
        mysql_credentials,
        mocker,
        faker,
        caplog,
        quiet,
    ):
        proc = SQLite3toMySQL(
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            quiet=quiet,
        )

        sqlite_engine = create_engine(
            "sqlite:///{database}".format(database=sqlite_database)
        )
        sqlite_inspect = inspect(sqlite_engine)
        sqlite_tables = sqlite_inspect.get_table_names()

        tables_with_indices = []
        for table in sqlite_tables:
            if sqlite_inspect.get_indexes(table):
                tables_with_indices.append(table)

        table_name = choice(tables_with_indices)
        proc._create_table(table_name)

        class FakeCursor:
            def execute(self, statement):
                raise mysql.connector.Error(
                    msg="Unknown MySQL error", errno=errorcode.CR_UNKNOWN_ERROR
                )

        mocker.patch.object(proc, "_mysql_cur", FakeCursor())

        with pytest.raises(mysql.connector.Error) as excinfo:
            caplog.set_level(logging.DEBUG)
            proc._add_indices(table_name)
        assert str(errorcode.CR_UNKNOWN_ERROR) in str(excinfo.value)
        assert any(
            str(errorcode.CR_UNKNOWN_ERROR) in message for message in caplog.messages
        )

    @pytest.mark.parametrize("quiet", [False, True])
    def test_add_foreign_keys_error(
        self,
        sqlite_database,
        mysql_database,
        mysql_credentials,
        mocker,
        faker,
        caplog,
        quiet,
    ):
        proc = SQLite3toMySQL(
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            quiet=quiet,
        )

        sqlite_engine = create_engine(
            "sqlite:///{database}".format(database=sqlite_database)
        )
        sqlite_inspect = inspect(sqlite_engine)
        sqlite_tables = sqlite_inspect.get_table_names()

        tables_with_foreign_keys = []

        for table in sqlite_tables:
            sqlite_fk_stmt = 'PRAGMA foreign_key_list("{table}")'.format(table=table)
            sqlite_fk_result = sqlite_engine.execute(sqlite_fk_stmt)
            if sqlite_fk_result.returns_rows:
                for _ in sqlite_fk_result:
                    tables_with_foreign_keys.append(table)
                    break

        table_name = choice(tables_with_foreign_keys)

        proc._create_table(table_name)

        class FakeCursor:
            def execute(self, statement):
                raise mysql.connector.Error(
                    msg="Unknown MySQL error", errno=errorcode.CR_UNKNOWN_ERROR
                )

        mocker.patch.object(proc, "_mysql_cur", FakeCursor())

        with pytest.raises(mysql.connector.Error) as excinfo:
            caplog.set_level(logging.DEBUG)
            proc._add_foreign_keys(table_name)
        assert str(errorcode.CR_UNKNOWN_ERROR) in str(excinfo.value)
        assert any(
            str(errorcode.CR_UNKNOWN_ERROR) in message for message in caplog.messages
        )
