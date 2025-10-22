import importlib
import logging
import re
import sys
import types
import typing as t
from random import choice

import mysql.connector
import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner, Result
from faker import Faker
from mysql.connector import errorcode
from pytest_mock import MockerFixture, MockFixture
from sqlalchemy import Connection, CursorResult, Engine, Inspector, TextClause, create_engine, inspect, text
from sqlalchemy.dialects.sqlite import __all__ as sqlite_column_types
from sqlglot import errors as sqlglot_errors
from sqlglot import expressions as exp

from sqlite3_to_mysql import SQLite3toMySQL
from sqlite3_to_mysql.cli import cli as sqlite3mysql
from tests.conftest import MySQLCredentials


def test_cli_sqlite_views_flag_propagates(
    cli_runner: CliRunner,
    sqlite_database: str,
    mysql_credentials: MySQLCredentials,
    mocker: MockerFixture,
) -> None:
    transporter_ctor = mocker.patch("sqlite3_to_mysql.cli.SQLite3toMySQL", autospec=True)
    transporter_instance = transporter_ctor.return_value
    transporter_instance.transfer.return_value = None

    common_args = [
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
        str(mysql_credentials.port),
    ]

    result: Result = cli_runner.invoke(sqlite3mysql, common_args)
    assert result.exit_code == 0
    assert transporter_ctor.call_count == 1
    assert transporter_ctor.call_args.kwargs["sqlite_views_as_tables"] is False

    transporter_ctor.reset_mock()
    transporter_instance = transporter_ctor.return_value
    transporter_instance.transfer.return_value = None

    result = cli_runner.invoke(sqlite3mysql, common_args + ["--sqlite-views-as-tables"])
    assert result.exit_code == 0
    assert transporter_ctor.call_count == 1
    assert transporter_ctor.call_args.kwargs["sqlite_views_as_tables"] is True


def test_cli_collation_validation(
    cli_runner: CliRunner,
    sqlite_database: str,
    mysql_credentials: MySQLCredentials,
    mocker: MockerFixture,
) -> None:
    mocker.patch(
        "sqlite3_to_mysql.cli.mysql_supported_character_sets",
        return_value=[types.SimpleNamespace(collation="utf8_general_ci")],
    )

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
            str(mysql_credentials.port),
            "--mysql-charset",
            "utf8mb4",
            "--mysql-collation",
            "utf8mb4_unicode_ci",
        ],
    )

    assert result.exit_code != 0
    assert "Invalid value for '--collation'" in result.output


def test_types_typed_dict_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    import typing

    import sqlite3_to_mysql.types as original_module

    monkeypatch.delattr(typing, "TypedDict", raising=False)
    monkeypatch.setitem(sys.modules, "typing_extensions", types.SimpleNamespace(TypedDict=object))
    sys.modules.pop("sqlite3_to_mysql.types", None)

    fallback_module = importlib.import_module("sqlite3_to_mysql.types")
    assert fallback_module.TypedDict is object

    sys.modules["sqlite3_to_mysql.types"] = original_module


def test_fetch_sqlite_master_rows_with_inclusion_filter(mocker: MockFixture) -> None:
    instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
    instance._sqlite_tables = ("kept",)
    instance._exclude_sqlite_tables = tuple()
    cursor = mocker.MagicMock()
    cursor.fetchall.return_value = [{"name": "kept", "type": "table", "sql": "CREATE TABLE kept (id INTEGER)"}]
    instance._sqlite_cur = cursor

    rows = instance._fetch_sqlite_master_rows(("table", "view"), include_sql=True)

    query, params = cursor.execute.call_args[0]
    flattened_query = " ".join(query.split())
    assert "type IN (?, ?)" in flattened_query
    assert "name IN (?)" in flattened_query
    assert params[-1] == "kept"
    assert rows == [{"name": "kept", "type": "table", "sql": "CREATE TABLE kept (id INTEGER)"}]


def test_fetch_sqlite_master_rows_with_exclusion_filter(mocker: MockFixture) -> None:
    instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
    instance._sqlite_tables = tuple()
    instance._exclude_sqlite_tables = ("skip_me",)
    cursor = mocker.MagicMock()
    cursor.fetchall.return_value = [{"name": "other", "type": "view"}]
    instance._sqlite_cur = cursor

    instance._fetch_sqlite_master_rows(("view",), include_sql=False)

    query, params = cursor.execute.call_args[0]
    flattened_query = " ".join(query.split())
    assert "name NOT IN (?)" in flattened_query
    assert params[-1] == "skip_me"


def test_sqlite_table_has_rowid_quotes(mocker: MockFixture) -> None:
    instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
    cursor = mocker.MagicMock()
    cursor.fetchall.return_value = []
    instance._sqlite_cur = cursor

    assert instance._sqlite_table_has_rowid('weird"name')
    cursor.execute.assert_called_once_with('SELECT rowid FROM "weird""name" LIMIT 1')


def test_fetch_sqlite_master_rows_without_types_returns_empty(mocker: MockFixture) -> None:
    instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
    instance._sqlite_cur = mocker.MagicMock()
    result = instance._fetch_sqlite_master_rows(tuple())
    assert result == []
    instance._sqlite_cur.execute.assert_not_called()


def test_create_mysql_view_success(mocker: MockFixture) -> None:
    instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
    cursor = mocker.MagicMock()
    mysql_conn = mocker.MagicMock()
    logger = mocker.MagicMock()
    instance._mysql_cur = cursor
    instance._mysql = mysql_conn
    instance._logger = logger

    instance._create_mysql_view("foo", "CREATE VIEW foo AS SELECT 1")

    assert cursor.execute.call_args_list[0][0][0] == "DROP TABLE IF EXISTS `foo`"
    assert cursor.execute.call_args_list[1][0][0] == "CREATE VIEW foo AS SELECT 1"
    assert mysql_conn.commit.call_count == 2
    logger.info.assert_called_once()


def test_create_mysql_view_ignores_known_drop_errors(mocker: MockFixture) -> None:
    instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
    cursor = mocker.MagicMock()
    mysql_conn = mocker.MagicMock()
    instance._mysql_cur = cursor
    instance._mysql = mysql_conn
    instance._logger = mocker.MagicMock()

    cursor.execute.side_effect = [
        mysql.connector.Error(msg="not a table", errno=errorcode.ER_WRONG_OBJECT),
        None,
    ]

    instance._create_mysql_view("foo", "CREATE VIEW foo AS SELECT 1")

    assert cursor.execute.call_args_list[1][0][0] == "CREATE VIEW foo AS SELECT 1"
    assert mysql_conn.commit.call_count == 1


def test_create_mysql_view_raises_unexpected_drop_errors(mocker: MockFixture) -> None:
    instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
    cursor = mocker.MagicMock()
    mysql_conn = mocker.MagicMock()
    instance._mysql_cur = cursor
    instance._mysql = mysql_conn
    instance._logger = mocker.MagicMock()

    cursor.execute.side_effect = mysql.connector.Error(msg="boom", errno=errorcode.CR_UNKNOWN_ERROR)

    with pytest.raises(mysql.connector.Error):
        instance._create_mysql_view("foo", "CREATE VIEW foo AS SELECT 1")

    cursor.execute.assert_called_once_with("DROP TABLE IF EXISTS `foo`")
    mysql_conn.commit.assert_not_called()


def test_translate_sqlite_view_definition_invalid_sql(mocker: MockFixture) -> None:
    instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
    mocker.patch(
        "sqlite3_to_mysql.transporter.sqlglot.parse_one",
        side_effect=sqlglot_errors.ParseError("boom"),
    )
    with pytest.raises(ValueError):
        instance._translate_sqlite_view_definition("broken", "CREATE VIEW broken AS SELECT")


def test_translate_sqlite_view_definition_render_error(mocker: MockFixture) -> None:
    instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
    fake_expression = mocker.MagicMock()
    fake_expression.set.return_value = fake_expression
    fake_expression.transform.return_value = fake_expression
    fake_expression.sql.side_effect = sqlglot_errors.SqlglotError("render fail")

    mocker.patch("sqlite3_to_mysql.transporter.sqlglot.parse_one", return_value=fake_expression)

    with pytest.raises(ValueError):
        instance._translate_sqlite_view_definition("v", "CREATE VIEW v AS SELECT 1")


def test_rewrite_sqlite_view_functions_datetime_now() -> None:
    node = exp.Anonymous(this=exp.Identifier(this="DATETIME"), expressions=[exp.Literal.string("now")])
    transformed = SQLite3toMySQL._rewrite_sqlite_view_functions(node)
    assert isinstance(transformed, exp.CurrentTimestamp)


def test_rewrite_sqlite_view_functions_strftime_now() -> None:
    node = exp.Anonymous(
        this=exp.Identifier(this="STRFTIME"),
        expressions=[exp.Literal.string("%H:%M:%S"), exp.Literal.string("now")],
    )
    transformed = SQLite3toMySQL._rewrite_sqlite_view_functions(node)
    assert isinstance(transformed, exp.TimeToStr)
    assert transformed.args["format"].this == "%H:%i:%s"
    assert "'%H:%i:%s')" in transformed.sql(dialect="mysql")


def test_rewrite_sqlite_view_functions_time_to_str() -> None:
    node = exp.TimeToStr(
        this=exp.TsOrDsToTimestamp(this=exp.Literal.string("now")),
        format=exp.Literal.string("%H:%M"),
    )
    transformed = SQLite3toMySQL._rewrite_sqlite_view_functions(node)
    assert isinstance(transformed, exp.TimeToStr)
    assert transformed.args["format"].this == "%H:%i"


def _make_transfer_stub(mocker: MockFixture) -> SQLite3toMySQL:
    instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
    instance._sqlite_tables = tuple()
    instance._exclude_sqlite_tables = tuple()
    instance._sqlite_views_as_tables = False
    instance._mysql_create_tables = True
    instance._mysql_transfer_data = False
    instance._mysql_truncate_tables = False
    instance._mysql_insert_method = "IGNORE"
    instance._mysql_version = "8.0.30"
    instance._without_foreign_keys = True
    instance._use_fulltext = False
    instance._mysql_fulltext_support = False
    instance._with_rowid = False
    instance._sqlite_cur = mocker.MagicMock()
    instance._sqlite_table_has_rowid = mocker.MagicMock(return_value=False)
    instance._mysql_cur = mocker.MagicMock()
    instance._mysql_cur.fetchall.return_value = []
    instance._mysql_cur.execute.return_value = None
    instance._mysql_cur.executemany.return_value = None
    instance._mysql = mocker.MagicMock()
    instance._logger = mocker.MagicMock()
    instance._create_table = mocker.MagicMock()
    instance._truncate_table = mocker.MagicMock()
    instance._add_indices = mocker.MagicMock()
    instance._add_foreign_keys = mocker.MagicMock()
    instance._transfer_table_data = mocker.MagicMock()
    instance._create_mysql_view = mocker.MagicMock()
    instance._translate_sqlite_view_definition = mocker.MagicMock(return_value="CREATE VIEW translated AS SELECT 1")
    instance._sqlite_cur.fetchall.return_value = []
    instance._sqlite_cur.execute.return_value = None
    return instance


def test_transfer_creates_mysql_views(mocker: MockFixture) -> None:
    instance = _make_transfer_stub(mocker)

    def fetch_rows(object_types, include_sql=False):
        if include_sql:
            return [{"name": "v1", "type": "view", "sql": "CREATE VIEW v1 AS SELECT 1"}]
        return [{"name": "t1", "type": "table"}]

    instance._fetch_sqlite_master_rows = mocker.MagicMock(side_effect=fetch_rows)

    instance.transfer()

    instance._create_table.assert_called_once_with("t1", transfer_rowid=False)
    instance._translate_sqlite_view_definition.assert_called_once_with("v1", "CREATE VIEW v1 AS SELECT 1")
    instance._create_mysql_view.assert_called_once_with("v1", "CREATE VIEW translated AS SELECT 1")


def test_transfer_handles_views_as_tables_when_requested(mocker: MockFixture) -> None:
    instance = _make_transfer_stub(mocker)
    instance._sqlite_views_as_tables = True

    def fetch_rows(object_types, include_sql=False):
        assert include_sql is False
        return [{"name": "view_as_table", "type": "view"}]

    instance._fetch_sqlite_master_rows = mocker.MagicMock(side_effect=fetch_rows)

    instance.transfer()

    instance._create_table.assert_called_once_with("view_as_table", transfer_rowid=False)
    instance._create_mysql_view.assert_not_called()


def test_transfer_with_data_invokes_transfer_table_data(mocker: MockFixture) -> None:
    instance = _make_transfer_stub(mocker)
    instance._mysql_transfer_data = True
    instance._sqlite_cur.fetchone.return_value = {"total_records": 1}
    instance._sqlite_cur.fetchall.return_value = [(1, 2)]

    def execute_side_effect(sql, *params):
        if sql.startswith("SELECT ") and "FROM" in sql and "COUNT" not in sql.upper():
            instance._sqlite_cur.description = [("c1",), ("c2",)]

    instance._sqlite_cur.execute.side_effect = execute_side_effect
    instance._fetch_sqlite_master_rows = mocker.MagicMock(side_effect=[[{"name": "tbl", "type": "table"}], []])

    instance.transfer()

    assert instance._transfer_table_data.called
    sql_arg = instance._transfer_table_data.call_args.kwargs["sql"]
    assert "INSERT" in sql_arg


def test_transfer_escapes_sqlite_identifiers(mocker: MockFixture) -> None:
    instance = _make_transfer_stub(mocker)
    instance._mysql_transfer_data = True
    instance._sqlite_cur.fetchone.return_value = {"total_records": 1}
    instance._sqlite_cur.fetchall.return_value = [(1,)]

    def execute_side_effect(sql, *params):
        if sql.startswith("SELECT ") and "FROM" in sql and "COUNT" not in sql.upper():
            instance._sqlite_cur.description = [("c1",)]
        return None

    instance._sqlite_cur.execute.side_effect = execute_side_effect
    instance._fetch_sqlite_master_rows = mocker.MagicMock(side_effect=[[{"name": 'tbl"quote', "type": "table"}], []])

    instance.transfer()

    executed_sqls = [call.args[0] for call in instance._sqlite_cur.execute.call_args_list]
    assert 'SELECT COUNT(*) AS total_records FROM "tbl""quote"' in executed_sqls
    assert 'SELECT * FROM "tbl""quote"' in executed_sqls


def test_translate_sqlite_view_definition_strftime_weekday() -> None:
    instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
    result = instance._translate_sqlite_view_definition(
        "v_week", "CREATE VIEW v_week AS SELECT strftime('%W %w', 'now') AS w"
    )
    assert "DATE_FORMAT(CURRENT_TIMESTAMP(), '%u %w')" in result


def test_translate_sqlite_view_definition_strftime_literal_percent() -> None:
    instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
    result = instance._translate_sqlite_view_definition(
        "v_literal", "CREATE VIEW v_literal AS SELECT strftime('%%Y %Y', 'now') AS f"
    )
    assert "DATE_FORMAT(CURRENT_TIMESTAMP(), '%%Y %Y')" in result


def test_transfer_skips_views_without_sql(mocker: MockFixture) -> None:
    instance = _make_transfer_stub(mocker)
    instance._fetch_sqlite_master_rows = mocker.MagicMock(
        side_effect=[
            [{"name": "tbl", "type": "table"}],
            [{"name": "v_bad", "type": "view", "sql": None}],
        ]
    )

    instance.transfer()

    instance._translate_sqlite_view_definition.assert_not_called()
    instance._create_mysql_view.assert_not_called()
    assert instance._logger.warning.called


def test_transfer_table_data_without_chunk(mocker: MockFixture) -> None:
    instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
    instance._chunk_size = None
    instance._quiet = True
    instance._sqlite_cur = mocker.MagicMock()
    instance._sqlite_cur.fetchall.return_value = [(1, 2), (3, 4)]
    instance._mysql_cur = mocker.MagicMock()
    instance._mysql = mocker.MagicMock()

    instance._transfer_table_data("INSERT", total_records=2)

    instance._mysql_cur.executemany.assert_called_once()
    instance._mysql.commit.assert_called_once()


def test_transfer_table_data_with_chunking(mocker: MockFixture) -> None:
    instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
    instance._chunk_size = 1
    instance._quiet = True
    instance._sqlite_cur = mocker.MagicMock()
    instance._sqlite_cur.fetchmany.side_effect = [[(1,)], [(2,)]]
    instance._mysql_cur = mocker.MagicMock()
    instance._mysql = mocker.MagicMock()

    instance._transfer_table_data("INSERT", total_records=2)

    assert instance._sqlite_cur.fetchmany.call_count == 2
    assert instance._mysql_cur.executemany.call_count == 2
    instance._mysql.commit.assert_called_once()


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

        for column in sqlite_column_types + ("INT64", "BOOL"):
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
            elif column in {"BOOL", "BOOLEAN"}:
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
        assert proc._translate_type_from_sqlite_to_mysql("DOUBLE PRECISION") == "DOUBLE PRECISION"
        assert proc._translate_type_from_sqlite_to_mysql("UNSIGNED BIG INT") == "BIGINT UNSIGNED"
        length = faker.pyint(min_value=1000000000, max_value=99999999999999999999)
        assert proc._translate_type_from_sqlite_to_mysql(f"UNSIGNED BIG INT({length})") == f"BIGINT({length}) UNSIGNED"
        assert proc._translate_type_from_sqlite_to_mysql("INT1") == "TINYINT"
        assert proc._translate_type_from_sqlite_to_mysql("INT2") == "SMALLINT"
        assert proc._translate_type_from_sqlite_to_mysql("INT3") == "MEDIUMINT"
        assert proc._translate_type_from_sqlite_to_mysql("INT4") == "INT"
        assert proc._translate_type_from_sqlite_to_mysql("INT8") == "BIGINT"
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

    @pytest.mark.parametrize(
        "sqlite_data_type, mysql_data_type",
        [
            ("INT", "INT(11)"),
            ("INT(5)", "INT(5)"),
            ("INT UNSIGNED", "INT(11) UNSIGNED"),
            ("INT(5) UNSIGNED", "INT(5) UNSIGNED"),
            ("INTEGER", "INT(11)"),
            ("TINYINT", "TINYINT"),
            ("TINYINT UNSIGNED", "TINYINT UNSIGNED"),
            ("TINYINT(4)", "TINYINT(4)"),
            ("TINYINT(4) UNSIGNED", "TINYINT(4) UNSIGNED"),
            ("SMALLINT", "SMALLINT"),
            ("SMALLINT UNSIGNED", "SMALLINT UNSIGNED"),
            ("SMALLINT(6)", "SMALLINT(6)"),
            ("SMALLINT(6) UNSIGNED", "SMALLINT(6) UNSIGNED"),
            ("MEDIUMINT", "MEDIUMINT"),
            ("MEDIUMINT UNSIGNED", "MEDIUMINT UNSIGNED"),
            ("MEDIUMINT(9)", "MEDIUMINT(9)"),
            ("MEDIUMINT(9) UNSIGNED", "MEDIUMINT(9) UNSIGNED"),
            ("BIGINT", "BIGINT"),
            ("BIGINT UNSIGNED", "BIGINT UNSIGNED"),
            ("BIGINT(20)", "BIGINT(20)"),
            ("BIGINT(20) UNSIGNED", "BIGINT(20) UNSIGNED"),
            ("UNSIGNED BIG INT", "BIGINT UNSIGNED"),
            ("INT1", "TINYINT"),
            ("INT1 UNSIGNED", "TINYINT UNSIGNED"),
            ("INT1(3)", "TINYINT(3)"),
            ("INT1(3) UNSIGNED", "TINYINT(3) UNSIGNED"),
            ("INT2", "SMALLINT"),
            ("INT2 UNSIGNED", "SMALLINT UNSIGNED"),
            ("INT2(6)", "SMALLINT(6)"),
            ("INT2(6) UNSIGNED", "SMALLINT(6) UNSIGNED"),
            ("INT3", "MEDIUMINT"),
            ("INT3 UNSIGNED", "MEDIUMINT UNSIGNED"),
            ("INT3(9)", "MEDIUMINT(9)"),
            ("INT3(9) UNSIGNED", "MEDIUMINT(9) UNSIGNED"),
            ("INT4", "INT"),
            ("INT4 UNSIGNED", "INT UNSIGNED"),
            ("INT4(11)", "INT(11)"),
            ("INT4(11) UNSIGNED", "INT(11) UNSIGNED"),
            ("INT8", "BIGINT"),
            ("INT8 UNSIGNED", "BIGINT UNSIGNED"),
            ("INT8(19)", "BIGINT(19)"),
            ("INT8(19) UNSIGNED", "BIGINT(19) UNSIGNED"),
            ("NUMERIC", "BIGINT(19)"),
            ("NUMERIC(10,5)", "DECIMAL(10,5)"),
            ("DOUBLE", "DOUBLE"),
            ("DOUBLE UNSIGNED", "DOUBLE UNSIGNED"),
            ("DOUBLE(10,5)", "DOUBLE(10,5)"),
            ("DOUBLE(10,5) UNSIGNED", "DOUBLE(10,5) UNSIGNED"),
            ("DOUBLE PRECISION", "DOUBLE PRECISION"),
            ("DOUBLE PRECISION UNSIGNED", "DOUBLE PRECISION UNSIGNED"),
            ("DOUBLE PRECISION(10,5)", "DOUBLE PRECISION(10,5)"),
            ("DOUBLE PRECISION(10,5) UNSIGNED", "DOUBLE PRECISION(10,5) UNSIGNED"),
            ("DECIMAL", "DECIMAL"),
            ("DECIMAL UNSIGNED", "DECIMAL UNSIGNED"),
            ("DECIMAL(10,5)", "DECIMAL(10,5)"),
            ("DECIMAL(10,5) UNSIGNED", "DECIMAL(10,5) UNSIGNED"),
            ("REAL", "REAL"),
            ("REAL UNSIGNED", "REAL UNSIGNED"),
            ("REAL(10,5)", "REAL(10,5)"),
            ("REAL(10,5) UNSIGNED", "REAL(10,5) UNSIGNED"),
            ("FLOAT", "FLOAT"),
            ("FLOAT UNSIGNED", "FLOAT UNSIGNED"),
            ("FLOAT(10,5)", "FLOAT(10,5)"),
            ("FLOAT(10,5) UNSIGNED", "FLOAT(10,5) UNSIGNED"),
            ("DEC", "DEC"),
            ("DEC UNSIGNED", "DEC UNSIGNED"),
            ("DEC(10,5)", "DEC(10,5)"),
            ("DEC(10,5) UNSIGNED", "DEC(10,5) UNSIGNED"),
            ("FIXED", "FIXED"),
            ("FIXED UNSIGNED", "FIXED UNSIGNED"),
            ("FIXED(10,5)", "FIXED(10,5)"),
            ("FIXED(10,5) UNSIGNED", "FIXED(10,5) UNSIGNED"),
            ("BOOL", "TINYINT(1)"),
            ("BOOLEAN", "TINYINT(1)"),
            ("INT64", "BIGINT(19)"),
        ],
    )
    def test_translate_type_from_sqlite_to_mysql_all_valid_numeric_columns_signed_unsigned(
        self,
        sqlite_database: str,
        mysql_database: Engine,
        mysql_credentials: MySQLCredentials,
        sqlite_data_type: str,
        mysql_data_type: str,
    ) -> None:
        proc: SQLite3toMySQL = SQLite3toMySQL(  # type: ignore
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
        )
        assert proc._translate_type_from_sqlite_to_mysql(sqlite_data_type) == mysql_data_type

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

    @pytest.mark.parametrize("quiet", [False, True])
    def test_add_index_duplicate_key_error(
        self,
        sqlite_database: str,
        mysql_database: Engine,
        mysql_credentials: MySQLCredentials,
        mocker: MockFixture,
        faker: Faker,
        caplog: LogCaptureFixture,
        quiet: bool,
    ) -> None:
        """Test handling of duplicate key errors in _add_index."""
        proc = SQLite3toMySQL(  # type: ignore[call-arg]
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            quiet=quiet,
            ignore_duplicate_keys=False,  # Don't ignore duplicate keys
        )

        # Create a mock cursor that raises a duplicate key error on first call
        # and succeeds on second call (for the renamed key)
        class FakeCursor:
            call_count = 0

            def execute(self, statement):
                self.call_count += 1
                if self.call_count == 1:
                    raise mysql.connector.Error(msg="Duplicate key name", errno=errorcode.ER_DUP_KEYNAME)
                # Second call should succeed
                return None

        fake_cursor = FakeCursor()
        mocker.patch.object(proc, "_mysql_cur", fake_cursor)

        # Mock MySQL connection commit
        mocker.patch.object(proc._mysql, "commit")

        # Create fake index info
        index = {"name": "test_index", "unique": 0}
        index_infos = ({"name": "test_column"},)

        caplog.set_level(logging.DEBUG)
        # Call _add_index - it should handle the duplicate key error and retry
        proc._add_index(
            table_name="test_table",
            index_type="INDEX",
            index=index,
            index_columns="test_column",
            index_infos=index_infos,
        )

        # Verify the cursor was called twice (once for original key, once for renamed)
        assert fake_cursor.call_count == 2

        # Verify warning was logged
        assert any("Duplicate key" in message for message in caplog.messages)
        assert any("Trying to create new key" in message for message in caplog.messages)

    @pytest.mark.parametrize("quiet", [False, True])
    def test_add_index_duplicate_key_error_ignored(
        self,
        sqlite_database: str,
        mysql_database: Engine,
        mysql_credentials: MySQLCredentials,
        mocker: MockFixture,
        faker: Faker,
        caplog: LogCaptureFixture,
        quiet: bool,
    ) -> None:
        """Test handling of duplicate key errors in _add_index when ignore_duplicate_keys is True."""
        proc = SQLite3toMySQL(  # type: ignore[call-arg]
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            quiet=quiet,
            ignore_duplicate_keys=True,  # Ignore duplicate keys
        )

        # Create a mock cursor that raises a duplicate key error
        class FakeCursor:
            def execute(self, statement):
                raise mysql.connector.Error(msg="Duplicate key name", errno=errorcode.ER_DUP_KEYNAME)

        mocker.patch.object(proc, "_mysql_cur", FakeCursor())

        # Create fake index info
        index = {"name": "test_index", "unique": 0}
        index_infos = ({"name": "test_column"},)

        caplog.set_level(logging.DEBUG)
        # Call _add_index - it should handle the duplicate key error and not retry
        proc._add_index(
            table_name="test_table",
            index_type="INDEX",
            index=index,
            index_columns="test_column",
            index_infos=index_infos,
        )

        # Verify warning was logged
        assert any("Ignoring duplicate key" in message for message in caplog.messages)

    @pytest.mark.parametrize("quiet", [False, True])
    def test_add_index_bad_fulltext_error(
        self,
        sqlite_database: str,
        mysql_database: Engine,
        mysql_credentials: MySQLCredentials,
        mocker: MockFixture,
        faker: Faker,
        caplog: LogCaptureFixture,
        quiet: bool,
    ) -> None:
        """Test handling of bad FULLTEXT index errors in _add_index."""
        proc = SQLite3toMySQL(  # type: ignore[call-arg]
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            quiet=quiet,
        )

        # Create a mock cursor that raises a bad FULLTEXT error
        class FakeCursor:
            def execute(self, statement):
                raise mysql.connector.Error(msg="Bad FULLTEXT column", errno=errorcode.ER_BAD_FT_COLUMN)

        mocker.patch.object(proc, "_mysql_cur", FakeCursor())

        # Create fake index info
        index = {"name": "test_index", "unique": 0}
        index_infos = ({"name": "test_column"},)

        caplog.set_level(logging.DEBUG)
        # Call _add_index with FULLTEXT index type
        with pytest.raises(mysql.connector.Error) as excinfo:
            proc._add_index(
                table_name="test_table",
                index_type="FULLTEXT",
                index=index,
                index_columns="test_column",
                index_infos=index_infos,
            )

        # Verify error was raised and warning was logged
        assert excinfo.value.errno == errorcode.ER_BAD_FT_COLUMN
        assert any("Failed adding FULLTEXT index" in message for message in caplog.messages)

    @pytest.mark.parametrize("quiet", [False, True])
    def test_transfer_finally_block(
        self,
        sqlite_database: str,
        mysql_database: Engine,
        mysql_credentials: MySQLCredentials,
        mocker: MockFixture,
        faker: Faker,
        caplog: LogCaptureFixture,
        quiet: bool,
    ) -> None:
        """Test the finally block in the transfer method."""
        proc = SQLite3toMySQL(  # type: ignore[call-arg]
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            quiet=quiet,
        )

        # Create a mock cursor that raises an exception during transfer
        class FakeCursor:
            execute_calls = []

            def execute(self, statement):
                self.execute_calls.append(statement)
                if "FOREIGN_KEY_CHECKS=0" in statement:
                    return None
                if "FOREIGN_KEY_CHECKS=1" in statement:
                    return None
                raise ValueError("Test error during transfer")

        fake_cursor = FakeCursor()
        mocker.patch.object(proc, "_mysql_cur", fake_cursor)

        # Call transfer - it should raise the ValueError but still execute FOREIGN_KEY_CHECKS=1
        with pytest.raises(ValueError) as excinfo:
            proc.transfer()

        # Verify error was raised
        assert str(excinfo.value) == "Test error during transfer"

        # Verify both FOREIGN_KEY_CHECKS statements were executed
        assert "FOREIGN_KEY_CHECKS=0" in fake_cursor.execute_calls[0]
        assert "FOREIGN_KEY_CHECKS=1" in fake_cursor.execute_calls[-1]

    @pytest.mark.parametrize(
        "expr, expected",
        [
            ("a", "a"),
            ("(a)", "a"),
            ("((a))", "a"),
            ("(((a)))", "a"),
            ("(a) + (b)", "(a) + (b)"),  # not fully wrapped; must remain unchanged
            ("((a) + (b))", "(a) + (b)"),  # fully wrapped once; strip one layer only
            (" ( ( a + b ) ) ", "a + b"),  # trims whitespace between iterations
            ("((CURRENT_TIMESTAMP))", "CURRENT_TIMESTAMP"),  # multiple full layers
            ("", ""),  # empty remains empty
            ("   ", ""),  # whitespace-only becomes empty
            ("(a", "(a"),  # unmatched; unchanged
            ("a)", "a)"),  # unmatched; unchanged
        ],
    )
    def test_strip_wrapping_parentheses(self, expr: str, expected: str) -> None:
        """Verify only fully wrapping outer parentheses are removed, repeatedly."""
        assert SQLite3toMySQL._strip_wrapping_parentheses(expr) == expected

    @staticmethod
    def _mk(*, expr: bool, ts_dt: bool, fsp: bool) -> SQLite3toMySQL:
        """
        Build a lightweight instance without hitting __init__ (no DB connection needed).
        Toggle the same feature flags transporter§ sets after version checks.
        """
        instance: SQLite3toMySQL = SQLite3toMySQL.__new__(SQLite3toMySQL)
        instance._allow_expr_defaults = expr  # MySQL >= 8.0.13
        instance._allow_current_ts_dt = ts_dt  # MySQL >= 5.6.5
        instance._allow_fsp = fsp  # MySQL >= 5.6.4
        return instance

    @pytest.mark.parametrize(
        "col, default, flags, expected",
        [
            # --- TIMESTAMP/DATETIME + CURRENT_TIMESTAMP / now() mapping ---
            # Too old for CURRENT_TIMESTAMP on TIMESTAMP: fall back to stripped expr
            ("TIMESTAMP(3)", "CURRENT_TIMESTAMP", {"expr": False, "ts_dt": False, "fsp": False}, "CURRENT_TIMESTAMP"),
            # Allowed, but no FSP support
            ("TIMESTAMP(3)", "CURRENT_TIMESTAMP", {"expr": False, "ts_dt": True, "fsp": False}, "CURRENT_TIMESTAMP"),
            # Allowed with FSP support -> keep precision
            ("TIMESTAMP(3)", "CURRENT_TIMESTAMP", {"expr": False, "ts_dt": True, "fsp": True}, "CURRENT_TIMESTAMP(3)"),
            # SQLite-style now -> map to CURRENT_TIMESTAMP (with FSP when allowed)
            ("DATETIME(2)", "datetime('now')", {"expr": False, "ts_dt": True, "fsp": True}, "CURRENT_TIMESTAMP(2)"),
            # --- DATE mapping (from 'now' forms or CURRENT_TIMESTAMP) ---
            # Only map when expression defaults are allowed
            ("DATE", "datetime('now')", {"expr": True, "ts_dt": False, "fsp": False}, "CURRENT_DATE"),
            ("DATE", "datetime('now')", {"expr": False, "ts_dt": False, "fsp": False}, "datetime('now')"),
            ("DATE", "CURRENT_TIMESTAMP", {"expr": True, "ts_dt": True, "fsp": True}, "CURRENT_DATE"),
            ("DATE", "CURRENT_TIMESTAMP", {"expr": False, "ts_dt": True, "fsp": True}, "CURRENT_TIMESTAMP"),
            # --- TIME mapping (from 'now' forms or CURRENT_TIMESTAMP) ---
            ("TIME(3)", "CURRENT_TIME", {"expr": True, "ts_dt": False, "fsp": True}, "CURRENT_TIME(3)"),
            ("TIME(3)", "CURRENT_TIME", {"expr": True, "ts_dt": False, "fsp": False}, "CURRENT_TIME"),
            ("TIME(6)", "CURRENT_TIMESTAMP", {"expr": True, "ts_dt": True, "fsp": True}, "CURRENT_TIME(6)"),
            ("TIME(6)", "CURRENT_TIMESTAMP", {"expr": False, "ts_dt": True, "fsp": True}, "CURRENT_TIMESTAMP"),
            # --- Boolean normalization (for BOOL/BOOLEAN/TINYINT) ---
            ("BOOLEAN", "TRUE", {"expr": False, "ts_dt": False, "fsp": False}, "1"),
            ("TINYINT(1)", "'FALSE'", {"expr": False, "ts_dt": False, "fsp": False}, "0"),
            # --- Numeric literals (incl. scientific notation) ---
            ("INT", "42", {"expr": False, "ts_dt": False, "fsp": False}, "42"),
            ("DOUBLE", "-3.14", {"expr": False, "ts_dt": False, "fsp": False}, "-3.14"),
            ("DOUBLE", "1e-3", {"expr": False, "ts_dt": False, "fsp": False}, "1e-3"),
            ("DOUBLE", "-2.5E+10", {"expr": False, "ts_dt": False, "fsp": False}, "-2.5E+10"),
            # --- Quoted strings and hex blobs pass through unchanged ---
            ("VARCHAR(10)", "'hello'", {"expr": False, "ts_dt": False, "fsp": False}, "'hello'"),
            ("BLOB", "X'ABCD'", {"expr": False, "ts_dt": False, "fsp": False}, "X'ABCD'"),
            # --- Expression fallback (strip fully wrapping parens, leave the expr) ---
            ("VARCHAR(10)", "(1+2)", {"expr": False, "ts_dt": False, "fsp": False}, "1+2"),
        ],
    )
    def test_translate_default_for_mysql(self, col: str, default: str, flags: t.Dict[str, bool], expected: str):
        assert self._mk(**flags)._translate_default_for_mysql(col, default) == expected

    def test_time_mapping_from_sqlite_now_respects_fsp(self):
        assert (
            self._mk(expr=True, ts_dt=False, fsp=True)._translate_default_for_mysql("TIME(2)", "time('now')")
            == "CURRENT_TIME(2)"
        )
        assert (
            self._mk(expr=True, ts_dt=False, fsp=False)._translate_default_for_mysql("TIME(2)", "time('now')")
            == "CURRENT_TIME"
        )

    def test_translate_sqlite_view_definition_current_timestamp(self):
        instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
        result = instance._translate_sqlite_view_definition(
            "v_now", "CREATE VIEW v_now AS SELECT datetime('now') AS stamp"
        )
        assert result == "CREATE OR REPLACE VIEW `v_now` AS SELECT CURRENT_TIMESTAMP() AS `stamp`"

    def test_translate_sqlite_view_definition_strftime_now(self):
        instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
        result = instance._translate_sqlite_view_definition(
            "v_fmt", "CREATE VIEW v_fmt AS SELECT strftime('%Y-%m-%d', 'now') AS d"
        )
        assert "DATE_FORMAT(CURRENT_TIMESTAMP(), '%Y-%m-%d')" in result

    def test_translate_sqlite_view_definition_strftime_minutes_seconds(self):
        instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
        result = instance._translate_sqlite_view_definition(
            "v_time", "CREATE VIEW v_time AS SELECT strftime('%H:%M:%S', 'now') AS t"
        )
        assert "DATE_FORMAT(CURRENT_TIMESTAMP(), '%H:%i:%s')" in result

    def test_translate_sqlite_view_definition_truncates_name(self):
        instance = SQLite3toMySQL.__new__(SQLite3toMySQL)
        long_name = "view_" + ("x" * 70)
        result = instance._translate_sqlite_view_definition(long_name, f"CREATE VIEW {long_name} AS SELECT 1")
        expected = long_name[:64]
        assert result == f"CREATE OR REPLACE VIEW `{expected}` AS SELECT 1"

    def test_init_chunk_parameter_conversion(
        self,
        sqlite_database: str,
        mysql_credentials: MySQLCredentials,
        mocker: MockFixture,
    ) -> None:
        """Verify chunk parameter is correctly converted to integer _chunk_size."""
        # Chunk=2 should yield _chunk_size == 2
        instance = SQLite3toMySQL(
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            chunk=2,
        )
        assert instance._chunk_size == 2

        # Chunk=None should yield _chunk_size == None
        instance = SQLite3toMySQL(
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            chunk=None,
        )
        assert instance._chunk_size is None
