import logging
import re
import typing as t
from collections import namedtuple
from itertools import chain
from pathlib import Path
from random import choice, sample

import mysql.connector
import pytest
import simplejson as json
from _pytest._py.path import LocalPath
from _pytest.capture import CaptureFixture
from _pytest.logging import LogCaptureFixture
from faker import Faker
from mysql.connector import MySQLConnection, errorcode
from mysql.connector.connection_cext import CMySQLConnection
from mysql.connector.pooling import PooledMySQLConnection
from pytest_mock import MockFixture
from sqlalchemy import MetaData, Table, create_engine, inspect, select, text
from sqlalchemy.engine import Connection, CursorResult, Engine, Inspector, Row
from sqlalchemy.engine.interfaces import ReflectedIndex
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import TextClause

from sqlite3_to_mysql import SQLite3toMySQL
from tests.conftest import Helpers, MySQLCredentials


@pytest.mark.usefixtures("sqlite_database", "mysql_instance")
class TestSQLite3toMySQL:
    @pytest.mark.init
    @pytest.mark.parametrize("quiet", [False, True])
    def test_no_sqlite_file_raises_exception(self, quiet: bool) -> None:
        with pytest.raises(ValueError) as excinfo:
            SQLite3toMySQL(quiet=quiet)  # type: ignore
        assert "Please provide an SQLite file" in str(excinfo.value)

    @pytest.mark.init
    @pytest.mark.parametrize("quiet", [False, True])
    def test_invalid_sqlite_file_raises_exception(self, faker: Faker, quiet: bool) -> None:
        with pytest.raises((FileNotFoundError, IOError)) as excinfo:
            SQLite3toMySQL(sqlite_file=faker.file_path(depth=1, extension=".sqlite3"), quiet=quiet)  # type: ignore[call-arg]
        assert "SQLite file does not exist" in str(excinfo.value)

    @pytest.mark.init
    @pytest.mark.parametrize("quiet", [False, True])
    def test_missing_mysql_user_raises_exception(self, sqlite_database: str, quiet: bool) -> None:
        with pytest.raises(ValueError) as excinfo:
            SQLite3toMySQL(sqlite_file=sqlite_database, quiet=quiet)  # type: ignore[call-arg]
        assert "Please provide a MySQL user" in str(excinfo.value)

    @pytest.mark.init
    @pytest.mark.parametrize("quiet", [False, True])
    def test_valid_sqlite_file_and_valid_mysql_credentials(
        self,
        sqlite_database: str,
        mysql_database: Engine,
        mysql_credentials: MySQLCredentials,
        helpers: Helpers,
        quiet: bool,
    ) -> None:
        with helpers.not_raises(FileNotFoundError):
            SQLite3toMySQL(  # type: ignore
                sqlite_file=sqlite_database,
                mysql_user=mysql_credentials.user,
                mysql_password=mysql_credentials.password,
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
                chunk=10,
                quiet=quiet,
            )

    @pytest.mark.init
    @pytest.mark.xfail
    @pytest.mark.parametrize("quiet", [False, True])
    def test_valid_sqlite_file_and_invalid_mysql_credentials_raises_access_denied_exception(
        self,
        sqlite_database: str,
        mysql_database: Engine,
        mysql_credentials: MySQLCredentials,
        faker: Faker,
        quiet: bool,
    ) -> None:
        with pytest.raises(mysql.connector.Error) as excinfo:
            SQLite3toMySQL(  # type: ignore[call-arg]
                sqlite_file=sqlite_database,
                mysql_user=faker.first_name().lower(),
                mysql_password=faker.password(length=16),
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
                quiet=quiet,
            )
        assert "Access denied for user" in str(excinfo.value)

    @pytest.mark.init
    @pytest.mark.xfail
    @pytest.mark.parametrize("quiet", [False, True])
    def test_unspecified_mysql_error(
        self,
        sqlite_database: str,
        mysql_credentials: MySQLCredentials,
        mocker: MockFixture,
        caplog: LogCaptureFixture,
        quiet: bool,
    ) -> None:
        mocker.patch.object(
            mysql.connector,
            "connect",
            side_effect=mysql.connector.Error(
                msg="Error Code: 2000. Unknown MySQL error",
                errno=errorcode.CR_UNKNOWN_ERROR,
            ),
        )
        caplog.set_level(logging.DEBUG)
        with pytest.raises(mysql.connector.Error) as excinfo:
            SQLite3toMySQL(  # type: ignore[call-arg]
                sqlite_file=sqlite_database,
                mysql_user=mysql_credentials.user,
                mysql_password=mysql_credentials.password,
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
                chunk=10,
                quiet=quiet,
            )
        assert str(errorcode.CR_UNKNOWN_ERROR) in str(excinfo.value)
        assert any(str(errorcode.CR_UNKNOWN_ERROR) in message for message in caplog.messages)

    @pytest.mark.init
    @pytest.mark.parametrize("quiet", [False, True])
    def test_bad_database_error(
        self,
        sqlite_database: str,
        mysql_credentials: MySQLCredentials,
        mocker: MockFixture,
        caplog: LogCaptureFixture,
        quiet: bool,
    ) -> None:
        class FakeMySQLConnection(MySQLConnection):
            @property
            def database(self):
                return self._database

            @database.setter
            def database(self, value):
                self._database = value
                # raise a fake exception
                raise mysql.connector.Error(msg="This is a test", errno=errorcode.ER_UNKNOWN_ERROR)

            def is_connected(self):
                return True

            def cursor(
                self,
                buffered=None,
                raw=None,
                prepared=None,
                cursor_class=None,
                dictionary=None,
                named_tuple=None,
            ):
                return True

        mocker.patch.object(mysql.connector, "connect", return_value=FakeMySQLConnection())
        with pytest.raises(mysql.connector.Error):
            caplog.set_level(logging.DEBUG)
            SQLite3toMySQL(  # type: ignore[call-arg]
                sqlite_file=sqlite_database,
                mysql_user=mysql_credentials.user,
                mysql_password=mysql_credentials.password,
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
                chunk=10,
                quiet=quiet,
            )

    @pytest.mark.init
    @pytest.mark.xfail
    @pytest.mark.parametrize("quiet", [False, True])
    def test_bad_mysql_connection(
        self, sqlite_database: str, mysql_credentials: MySQLCredentials, mocker: MockFixture, quiet: bool
    ) -> None:
        FakeConnector = namedtuple("FakeConnector", ["is_connected"])
        mocker.patch.object(
            mysql.connector,
            "connect",
            return_value=FakeConnector(is_connected=lambda: False),
        )
        with pytest.raises((ConnectionError, IOError)) as excinfo:
            SQLite3toMySQL(  # type: ignore[call-arg]
                sqlite_file=sqlite_database,
                mysql_user=mysql_credentials.user,
                mysql_password=mysql_credentials.password,
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
                chunk=10,
                quiet=quiet,
            )
        assert "Unable to connect to MySQL" in str(excinfo.value)

    @pytest.mark.init
    @pytest.mark.parametrize("quiet", [False, True])
    def test_mysql_skip_create_tables_and_transfer_data(
        self,
        sqlite_database: str,
        mysql_credentials: MySQLCredentials,
        mocker: MockFixture,
        quiet: bool,
    ) -> None:
        mocker.patch.object(
            SQLite3toMySQL,
            "transfer",
            return_value=None,
        )
        with pytest.raises(ValueError) as excinfo:
            SQLite3toMySQL(  # type: ignore[call-arg]
                sqlite_file=sqlite_database,
                mysql_user=mysql_credentials.user,
                mysql_password=mysql_credentials.password,
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
                mysql_create_tables=False,
                mysql_transfer_data=False,
                quiet=quiet,
            )
        assert "Unable to continue without transferring data or creating tables!" in str(excinfo.value)

    @pytest.mark.xfail
    @pytest.mark.init
    @pytest.mark.parametrize("quiet", [False, True])
    def test_log_to_file(
        self,
        sqlite_database: str,
        mysql_database: Engine,
        mysql_credentials: MySQLCredentials,
        faker: Faker,
        caplog: LogCaptureFixture,
        tmpdir: LocalPath,
        quiet: bool,
    ):
        log_file: LocalPath = tmpdir.join(Path("db.log"))
        with pytest.raises(mysql.connector.Error):
            caplog.set_level(logging.DEBUG)
            SQLite3toMySQL(  # type: ignore[call-arg]
                sqlite_file=sqlite_database,
                mysql_user=faker.first_name().lower(),
                mysql_password=faker.password(length=16),
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
                log_file=str(log_file),
                quiet=quiet,
            )
        assert any("Access denied for user" in message for message in caplog.messages)
        with log_file.open("r") as log_fh:
            log: str = log_fh.read()
            if len(caplog.messages) > 1:
                assert caplog.messages[1] in log
            else:
                assert caplog.messages[0] in log
            assert re.match(r"^\d{4,}-\d{2,}-\d{2,}\s+\d{2,}:\d{2,}:\d{2,}\s+\w+\s+", log) is not None

    @pytest.mark.transfer
    @pytest.mark.parametrize(
        "chunk, with_rowid, mysql_insert_method, ignore_duplicate_keys",
        [
            (None, False, "IGNORE", False),
            (None, False, "IGNORE", True),
            (None, False, "UPDATE", True),
            (None, False, "UPDATE", False),
            (None, False, "DEFAULT", True),
            (None, False, "DEFAULT", False),
            (None, True, "IGNORE", False),
            (None, True, "IGNORE", True),
            (None, True, "UPDATE", True),
            (None, True, "UPDATE", False),
            (None, True, "DEFAULT", True),
            (None, True, "DEFAULT", False),
            (10, False, "IGNORE", False),
            (10, False, "IGNORE", True),
            (10, False, "UPDATE", True),
            (10, False, "UPDATE", False),
            (10, False, "DEFAULT", True),
            (10, False, "DEFAULT", False),
            (10, True, "IGNORE", False),
            (10, True, "IGNORE", True),
            (10, True, "UPDATE", True),
            (10, True, "UPDATE", False),
            (10, True, "DEFAULT", True),
            (10, True, "DEFAULT", False),
        ],
    )
    def test_transfer_transfers_all_tables_in_sqlite_file(
        self,
        sqlite_database: str,
        mysql_database: Engine,
        mysql_credentials: MySQLCredentials,
        helpers: Helpers,
        capsys: CaptureFixture,
        caplog: LogCaptureFixture,
        chunk: t.Optional[int],
        with_rowid: bool,
        mysql_insert_method: str,
        ignore_duplicate_keys: bool,
    ):
        proc: SQLite3toMySQL = SQLite3toMySQL(  # type: ignore[call-arg]
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            chunk=chunk,
            with_rowid=with_rowid,
            mysql_insert_method=mysql_insert_method,
            ignore_duplicate_keys=ignore_duplicate_keys,
        )
        caplog.set_level(logging.DEBUG)
        proc.transfer()
        assert all(record.levelname == "INFO" for record in caplog.records)
        assert not any(record.levelname == "ERROR" for record in caplog.records)
        out, err = capsys.readouterr()

        sqlite_engine: Engine = create_engine(
            f"sqlite:///{sqlite_database}",
            json_serializer=json.dumps,
            json_deserializer=json.loads,
        )
        sqlite_cnx: Connection = sqlite_engine.connect()
        sqlite_inspect: Inspector = inspect(sqlite_engine)
        sqlite_tables: t.List[str] = sqlite_inspect.get_table_names()
        mysql_engine: Engine = create_engine(
            f"mysql+pymysql://{mysql_credentials.user}:{mysql_credentials.password}@{mysql_credentials.host}:{mysql_credentials.port}/{mysql_credentials.database}",
            json_serializer=json.dumps,
            json_deserializer=json.loads,
        )
        mysql_cnx: Connection = mysql_engine.connect()
        mysql_inspect: Inspector = inspect(mysql_engine)
        mysql_tables: t.List[str] = mysql_inspect.get_table_names()

        mysql_connector_connection: t.Union[PooledMySQLConnection, MySQLConnection, CMySQLConnection] = (
            mysql.connector.connect(
                user=mysql_credentials.user,
                password=mysql_credentials.password,
                host=mysql_credentials.host,
                port=mysql_credentials.port,
                database=mysql_credentials.database,
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci",
            )
        )
        server_version: t.Tuple[int, ...] = mysql_connector_connection.get_server_version()

        """ Test if both databases have the same table names """
        assert sqlite_tables == mysql_tables

        """ Test if all the tables have the same column names """
        for table_name in sqlite_tables:
            column_names: t.List[str] = [column["name"] for column in sqlite_inspect.get_columns(table_name)]
            if with_rowid:
                column_names.insert(0, "rowid")
            assert column_names == [column["name"] for column in mysql_inspect.get_columns(table_name)]

        """ Test if all the tables have the same indices """
        index_keys: t.Tuple[str, ...] = ("name", "column_names", "unique")
        mysql_indices: t.Tuple[ReflectedIndex, ...] = tuple(
            t.cast(ReflectedIndex, {key: index[key] for key in index_keys})  # type: ignore[literal-required]
            for index in (chain.from_iterable(mysql_inspect.get_indexes(table_name) for table_name in mysql_tables))
        )

        for table_name in sqlite_tables:
            sqlite_indices: t.List[ReflectedIndex] = sqlite_inspect.get_indexes(table_name)
            if with_rowid:
                sqlite_indices.insert(
                    0,
                    ReflectedIndex(
                        name=f"{table_name}_rowid",
                        column_names=["rowid"],
                        unique=True,
                    ),
                )
            for sqlite_index in sqlite_indices:
                sqlite_index["unique"] = bool(sqlite_index["unique"])
                if "dialect_options" in sqlite_index:
                    sqlite_index.pop("dialect_options", None)
                assert sqlite_index in mysql_indices

        """ Test if all the tables have the same foreign keys """
        for table_name in sqlite_tables:
            mysql_fk_stmt: TextClause = text(
                """
                SELECT k.REFERENCED_TABLE_NAME AS `table`, k.COLUMN_NAME AS `from`, k.REFERENCED_COLUMN_NAME AS `to`
                FROM information_schema.TABLE_CONSTRAINTS AS i
                {JOIN} information_schema.KEY_COLUMN_USAGE AS k ON i.CONSTRAINT_NAME = k.CONSTRAINT_NAME
                WHERE i.TABLE_SCHEMA = :table_schema
                AND i.TABLE_NAME = :table_name
                AND i.CONSTRAINT_TYPE = :constraint_type
            """.format(
                    # MySQL 8.0.19 still works with "LEFT JOIN" everything above requires "JOIN"
                    JOIN="JOIN" if (server_version[0] == 8 and server_version[2] > 19) else "LEFT JOIN"
                )
            ).bindparams(
                table_schema=mysql_credentials.database,
                table_name=table_name,
                constraint_type="FOREIGN KEY",
            )
            mysql_fk_result: CursorResult = mysql_cnx.execute(mysql_fk_stmt)
            mysql_foreign_keys: t.List[t.Dict[str, t.Any]] = [
                {
                    "table": fk["table"],
                    "from": fk["from"],
                    "to": fk["to"],
                }
                for fk in mysql_fk_result.mappings()
            ]

            sqlite_fk_stmt: TextClause = text(f'PRAGMA foreign_key_list("{table_name}")')
            sqlite_fk_result = sqlite_cnx.execute(sqlite_fk_stmt)
            if sqlite_fk_result.returns_rows:
                for fk in sqlite_fk_result.mappings():
                    assert {
                        "table": fk["table"],
                        "from": fk["from"],
                        "to": fk["to"],
                    } in mysql_foreign_keys

        """ Check if all the data was transferred correctly """
        sqlite_results: t.List[t.Tuple[t.Tuple[t.Any, ...], ...]] = []
        mysql_results: t.List[t.Tuple[t.Tuple[t.Any, ...], ...]] = []

        meta: MetaData = MetaData()
        for table_name in sqlite_tables:
            sqlite_table: Table = Table(table_name, meta, autoload_with=sqlite_engine)
            sqlite_stmt: Select = select(sqlite_table)
            sqlite_result: t.List[Row[t.Any]] = list(sqlite_cnx.execute(sqlite_stmt).fetchall())
            sqlite_result.sort()
            sqlite_results.append(tuple(tuple(data for data in row) for row in sqlite_result))

        for table_name in mysql_tables:
            mysql_table: Table = Table(table_name, meta, autoload_with=mysql_engine)
            mysql_stmt: Select = select(mysql_table)
            mysql_result: t.List[Row[t.Any]] = list(mysql_cnx.execute(mysql_stmt).fetchall())
            mysql_result.sort()
            mysql_results.append(tuple(tuple(data for data in row) for row in mysql_result))

        assert sqlite_results == mysql_results

        mysql_cnx.close()
        sqlite_cnx.close()
        mysql_engine.dispose()
        sqlite_engine.dispose()

    @pytest.mark.transfer
    @pytest.mark.parametrize(
        "chunk, with_rowid, mysql_insert_method, ignore_duplicate_keys",
        [
            (None, False, "IGNORE", False),
            (None, False, "IGNORE", True),
            (None, False, "UPDATE", True),
            (None, False, "UPDATE", False),
            (None, False, "DEFAULT", True),
            (None, False, "DEFAULT", False),
            (None, True, "IGNORE", False),
            (None, True, "IGNORE", True),
            (None, True, "UPDATE", True),
            (None, True, "UPDATE", False),
            (None, True, "DEFAULT", True),
            (None, True, "DEFAULT", False),
            (10, False, "IGNORE", False),
            (10, False, "IGNORE", True),
            (10, False, "UPDATE", True),
            (10, False, "UPDATE", False),
            (10, False, "DEFAULT", True),
            (10, False, "DEFAULT", False),
            (10, True, "IGNORE", False),
            (10, True, "IGNORE", True),
            (10, True, "UPDATE", True),
            (10, True, "UPDATE", False),
            (10, True, "DEFAULT", True),
            (10, True, "DEFAULT", False),
        ],
    )
    def test_transfer_specific_tables_transfers_only_specified_tables_from_sqlite_file(
        self,
        sqlite_database: str,
        mysql_database: Engine,
        mysql_credentials: MySQLCredentials,
        helpers: Helpers,
        capsys: CaptureFixture,
        caplog: LogCaptureFixture,
        chunk: t.Optional[int],
        with_rowid: bool,
        mysql_insert_method: str,
        ignore_duplicate_keys: bool,
    ) -> None:
        sqlite_engine: Engine = create_engine(
            f"sqlite:///{sqlite_database}",
            json_serializer=json.dumps,
            json_deserializer=json.loads,
        )
        sqlite_cnx: Connection = sqlite_engine.connect()
        sqlite_inspect: Inspector = inspect(sqlite_engine)
        sqlite_tables: t.List[str] = sqlite_inspect.get_table_names()

        table_number: int = choice(range(1, len(sqlite_tables)))

        random_sqlite_tables: t.List[str] = sample(sqlite_tables, table_number)
        random_sqlite_tables.sort()

        proc: SQLite3toMySQL = SQLite3toMySQL(  # type: ignore[call-arg]
            sqlite_file=sqlite_database,
            sqlite_tables=random_sqlite_tables,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            chunk=chunk,
            with_rowid=with_rowid,
            mysql_insert_method=mysql_insert_method,
            ignore_duplicate_keys=ignore_duplicate_keys,
        )
        caplog.set_level(logging.DEBUG)
        proc.transfer()
        assert all(record.levelname == "INFO" for record in caplog.records)
        assert not any(record.levelname == "ERROR" for record in caplog.records)
        out, err = capsys.readouterr()

        mysql_engine: Engine = create_engine(
            f"mysql+pymysql://{mysql_credentials.user}:{mysql_credentials.password}@{mysql_credentials.host}:{mysql_credentials.port}/{mysql_credentials.database}",
            json_serializer=json.dumps,
            json_deserializer=json.loads,
        )
        mysql_cnx: Connection = mysql_engine.connect()
        mysql_inspect: Inspector = inspect(mysql_engine)
        mysql_tables: t.List[str] = mysql_inspect.get_table_names()

        """ Test if both databases have the same table names """
        assert random_sqlite_tables == mysql_tables

        """ Test if all the tables have the same column names """
        for table_name in random_sqlite_tables:
            column_names: t.List[t.Any] = [column["name"] for column in sqlite_inspect.get_columns(table_name)]
            if with_rowid:
                column_names.insert(0, "rowid")
            assert column_names == [column["name"] for column in mysql_inspect.get_columns(table_name)]

        """ Test if all the tables have the same indices """
        index_keys: t.Tuple[str, ...] = ("name", "column_names", "unique")
        mysql_indices: t.Tuple[ReflectedIndex, ...] = tuple(
            t.cast(ReflectedIndex, {key: index[key] for key in index_keys})  # type: ignore[literal-required]
            for index in (chain.from_iterable(mysql_inspect.get_indexes(table_name) for table_name in mysql_tables))
        )

        for table_name in random_sqlite_tables:
            sqlite_indices: t.List[ReflectedIndex] = sqlite_inspect.get_indexes(table_name)
            if with_rowid:
                sqlite_indices.insert(
                    0,
                    ReflectedIndex(
                        name=f"{table_name}_rowid",
                        column_names=["rowid"],
                        unique=True,
                    ),
                )
            for sqlite_index in sqlite_indices:
                sqlite_index["unique"] = bool(sqlite_index["unique"])
                if "dialect_options" in sqlite_index:
                    sqlite_index.pop("dialect_options", None)
                assert sqlite_index in mysql_indices

        """ Check if all the data was transferred correctly """
        sqlite_results: t.List[t.Tuple[t.Tuple[t.Any, ...], ...]] = []
        mysql_results: t.List[t.Tuple[t.Tuple[t.Any, ...], ...]] = []

        meta: MetaData = MetaData()
        for table_name in random_sqlite_tables:
            sqlite_table: Table = Table(table_name, meta, autoload_with=sqlite_engine)
            sqlite_stmt: Select = select(sqlite_table)
            sqlite_result: t.List[Row[t.Any]] = list(sqlite_cnx.execute(sqlite_stmt).fetchall())
            sqlite_result.sort()
            sqlite_results.append(tuple(tuple(data for data in row) for row in sqlite_result))

        for table_name in mysql_tables:
            mysql_table: Table = Table(table_name, meta, autoload_with=mysql_engine)
            mysql_stmt: Select = select(mysql_table)
            mysql_result: t.List[Row[t.Any]] = list(mysql_cnx.execute(mysql_stmt).fetchall())
            mysql_result.sort()
            mysql_results.append(tuple(tuple(data for data in row) for row in mysql_result))

        assert sqlite_results == mysql_results

        mysql_cnx.close()
        sqlite_cnx.close()
        mysql_engine.dispose()
        sqlite_engine.dispose()
