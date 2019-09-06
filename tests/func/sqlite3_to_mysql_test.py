import logging
import re
from collections import namedtuple
from itertools import chain

import mysql.connector
import pytest
import simplejson as json
import six
from mysql.connector import errorcode, MySQLConnection
from sqlalchemy import create_engine, inspect, MetaData, Table, select, text

from sqlite3_to_mysql import SQLite3toMySQL

if six.PY2:
    from ..sixeptions import *


@pytest.mark.usefixtures("sqlite_database", "mysql_instance")
class TestSQLite3toMySQL:
    @pytest.mark.init
    def test_no_sqlite_file_raises_exception(self):
        with pytest.raises(ValueError) as excinfo:
            SQLite3toMySQL()
        assert "Please provide an SQLite file" in str(excinfo.value)

    @pytest.mark.init
    def test_invalid_sqlite_file_raises_exception(self, faker):
        with pytest.raises((FileNotFoundError, IOError)) as excinfo:
            SQLite3toMySQL(sqlite_file=faker.file_path(depth=1, extension=".sqlite3"))
        assert "SQLite file does not exist" in str(excinfo.value)

    @pytest.mark.init
    def test_missing_mysql_user_raises_exception(self, sqlite_database):
        with pytest.raises(ValueError) as excinfo:
            SQLite3toMySQL(sqlite_file=sqlite_database)
        assert "Please provide a MySQL user" in str(excinfo.value)

    @pytest.mark.init
    def test_valid_sqlite_file_and_valid_mysql_credentials(
        self, sqlite_database, mysql_database, mysql_credentials, helpers
    ):
        with helpers.not_raises(FileNotFoundError):
            SQLite3toMySQL(
                sqlite_file=sqlite_database,
                mysql_user=mysql_credentials.user,
                mysql_password=mysql_credentials.password,
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
                chunk=10,
            )

    @pytest.mark.init
    def test_valid_sqlite_file_and_invalid_mysql_credentials_raises_access_denied_exception(
        self, sqlite_database, mysql_database, mysql_credentials, faker
    ):
        with pytest.raises(mysql.connector.Error) as excinfo:
            SQLite3toMySQL(
                sqlite_file=sqlite_database,
                mysql_user=faker.first_name().lower(),
                mysql_password=faker.password(length=16),
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
            )
        assert "Access denied for user" in str(excinfo.value)

    @pytest.mark.init
    def test_unspecified_mysql_error(
        self, sqlite_database, mysql_credentials, mocker, caplog
    ):
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
            SQLite3toMySQL(
                sqlite_file=sqlite_database,
                mysql_user=mysql_credentials.user,
                mysql_password=mysql_credentials.password,
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
                chunk=10,
            )
        assert str(errorcode.CR_UNKNOWN_ERROR) in str(excinfo.value)
        assert any(
            str(errorcode.CR_UNKNOWN_ERROR) in message for message in caplog.messages
        )

    def test_bad_database_error(
        self, sqlite_database, mysql_credentials, mocker, caplog
    ):
        class FakeMySQLConnection(MySQLConnection):
            @property
            def database(self):
                return self._database

            @database.setter
            def database(self, value):
                self._database = value
                # raise a fake exception
                raise mysql.connector.Error(
                    msg="This is a test", errno=errorcode.ER_SERVER_TEST_MESSAGE
                )

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

        mocker.patch.object(
            mysql.connector, "connect", return_value=FakeMySQLConnection()
        )
        with pytest.raises(mysql.connector.Error):
            caplog.set_level(logging.DEBUG)
            SQLite3toMySQL(
                sqlite_file=sqlite_database,
                mysql_user=mysql_credentials.user,
                mysql_password=mysql_credentials.password,
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
                chunk=10,
            )

    @pytest.mark.init
    def test_bad_mysql_connection(self, sqlite_database, mysql_credentials, mocker):
        FakeConnector = namedtuple("FakeConnector", ["is_connected"])
        mocker.patch.object(
            mysql.connector,
            "connect",
            return_value=FakeConnector(is_connected=lambda: False),
        )
        with pytest.raises((ConnectionError, IOError)) as excinfo:
            SQLite3toMySQL(
                sqlite_file=sqlite_database,
                mysql_user=mysql_credentials.user,
                mysql_password=mysql_credentials.password,
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
                chunk=10,
            )
        assert "Unable to connect to MySQL" in str(excinfo.value)

    @pytest.mark.init
    def test_log_to_file(
        self, sqlite_database, mysql_database, mysql_credentials, faker, caplog, tmpdir
    ):
        log_file = tmpdir.join("db.log")
        with pytest.raises(mysql.connector.Error):
            caplog.set_level(logging.DEBUG)
            SQLite3toMySQL(
                sqlite_file=sqlite_database,
                mysql_user=faker.first_name().lower(),
                mysql_password=faker.password(length=16),
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
                log_file=str(log_file),
            )
        assert any("Access denied for user" in message for message in caplog.messages)
        with log_file.open("r") as log_fh:
            log = log_fh.read()
            assert caplog.messages[0] in log
            assert (
                re.match(r"^\d{4,}-\d{2,}-\d{2,}\s+\d{2,}:\d{2,}:\d{2,}\s+\w+\s+", log)
                is not None
            )

    @pytest.mark.transfer
    @pytest.mark.parametrize("chunk", [None, 10])
    def test_transfer_transfers_all_tables_in_sqlite_file(
        self,
        sqlite_database,
        mysql_database,
        mysql_credentials,
        helpers,
        capsys,
        caplog,
        chunk,
    ):
        proc = SQLite3toMySQL(
            sqlite_file=sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            chunk=chunk,
        )
        caplog.set_level(logging.DEBUG)
        proc.transfer()
        assert all(record.levelname == "INFO" for record in caplog.records)
        assert not any(record.levelname == "ERROR" for record in caplog.records)
        out, err = capsys.readouterr()

        sqlite_engine = create_engine(
            "sqlite:///{database}".format(database=sqlite_database),
            json_serializer=json.dumps,
            json_deserializer=json.loads,
        )
        sqlite_cnx = sqlite_engine.connect()
        sqlite_inspect = inspect(sqlite_engine)
        sqlite_tables = sqlite_inspect.get_table_names()
        mysql_engine = create_engine(
            "mysql+mysqldb://{user}:{password}@{host}:{port}/{database}".format(
                user=mysql_credentials.user,
                password=mysql_credentials.password,
                host=mysql_credentials.host,
                port=mysql_credentials.port,
                database=mysql_credentials.database,
            ),
            json_serializer=json.dumps,
            json_deserializer=json.loads,
        )
        mysql_cnx = mysql_engine.connect()
        mysql_inspect = inspect(mysql_engine)
        mysql_tables = mysql_inspect.get_table_names()

        """ Test if both databases have the same table names """
        assert sqlite_tables == mysql_tables

        """ Test if all the tables have the same column names """
        for table_name in sqlite_tables:
            assert [
                column["name"] for column in sqlite_inspect.get_columns(table_name)
            ] == [column["name"] for column in mysql_inspect.get_columns(table_name)]

        """ Test if all the tables have the same indices """
        index_keys = ("name", "column_names", "unique")
        mysql_indices = tuple(
            {key: index[key] for key in index_keys}
            for index in (
                chain.from_iterable(
                    mysql_inspect.get_indexes(table_name) for table_name in mysql_tables
                )
            )
        )

        for table_name in sqlite_tables:
            for sqlite_index in sqlite_inspect.get_indexes(table_name):
                sqlite_index["unique"] = bool(sqlite_index["unique"])
                assert sqlite_index in mysql_indices

        """ Test if all the tables have the same foreign keys """
        for table_name in sqlite_tables:
            mysql_fk_stmt = text(
                """
                SELECT k.REFERENCED_TABLE_NAME AS `table`, k.COLUMN_NAME AS `from`, k.REFERENCED_COLUMN_NAME AS `to`
                FROM information_schema.TABLE_CONSTRAINTS AS i 
                LEFT JOIN information_schema.KEY_COLUMN_USAGE AS k ON i.CONSTRAINT_NAME = k.CONSTRAINT_NAME 
                WHERE i.TABLE_SCHEMA = :table_schema
                AND i.TABLE_NAME = :table_name
                AND i.CONSTRAINT_TYPE = :constraint_type
            """
            ).bindparams(
                table_schema=mysql_credentials.database,
                table_name=table_name,
                constraint_type="FOREIGN KEY",
            )
            mysql_fk_result = mysql_cnx.execute(mysql_fk_stmt)
            mysql_foreign_keys = [dict(row) for row in mysql_fk_result]

            sqlite_fk_stmt = 'PRAGMA foreign_key_list("{table}")'.format(
                table=table_name
            )
            sqlite_fk_result = sqlite_cnx.execute(sqlite_fk_stmt)
            if sqlite_fk_result.returns_rows:
                for row in sqlite_fk_result:
                    fk = dict(row)
                    assert {
                        "table": fk["table"],
                        "from": fk["from"],
                        "to": fk["to"],
                    } in mysql_foreign_keys

        """ Check if all the data was transferred correctly """
        sqlite_results = []
        mysql_results = []

        meta = MetaData(bind=None)
        for table_name in sqlite_tables:
            sqlite_table = Table(
                table_name, meta, autoload=True, autoload_with=sqlite_engine
            )
            sqlite_stmt = select([sqlite_table])
            sqlite_result = sqlite_cnx.execute(sqlite_stmt).fetchall()
            sqlite_result.sort()
            sqlite_result = tuple(tuple(data for data in row) for row in sqlite_result)
            sqlite_results.append(sqlite_result)

        for table_name in mysql_tables:
            mysql_table = Table(
                table_name, meta, autoload=True, autoload_with=mysql_engine
            )
            mysql_stmt = select([mysql_table])
            mysql_result = mysql_cnx.execute(mysql_stmt).fetchall()
            mysql_result.sort()
            mysql_result = tuple(tuple(data for data in row) for row in mysql_result)
            mysql_results.append(mysql_result)

        assert sqlite_results == mysql_results
