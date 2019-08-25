import logging
import re
from collections import namedtuple

import mysql.connector
import pytest
from mysql.connector import errorcode
from sqlalchemy import create_engine, inspect, MetaData, Table, select

from src.sqlite3_to_mysql import SQLite3toMySQL


@pytest.mark.usefixtures("fake_sqlite_database", "docker_mysql")
class TestSQLite3toMySQL:
    @pytest.mark.init
    def test_no_sqlite_file_raises_exception(self):
        with pytest.raises(ValueError) as excinfo:
            SQLite3toMySQL()
        assert "Please provide an SQLite file" in str(excinfo.value)

    @pytest.mark.init
    def test_invalid_sqlite_file_raises_exception(self, faker):
        with pytest.raises(FileNotFoundError) as excinfo:
            SQLite3toMySQL(sqlite_file=faker.file_path(depth=1, extension=".sqlite3"))
        assert "SQLite file does not exist" in str(excinfo.value)

    @pytest.mark.init
    def test_missing_mysql_user_raises_exception(self, fake_sqlite_database):
        with pytest.raises(ValueError) as excinfo:
            SQLite3toMySQL(sqlite_file=fake_sqlite_database)
        assert "Please provide a MySQL user" in str(excinfo.value)

    @pytest.mark.init
    def test_valid_sqlite_file_and_valid_mysql_credentials(
        self, fake_sqlite_database, fake_mysql_database, mysql_credentials, helpers
    ):
        with helpers.not_raises(FileNotFoundError):
            SQLite3toMySQL(
                sqlite_file=fake_sqlite_database,
                mysql_user=mysql_credentials.user,
                mysql_password=mysql_credentials.password,
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
                chunk=1000,
            )

    @pytest.mark.init
    def test_valid_sqlite_file_and_invalid_mysql_credentials_raises_access_denied_exception(
        self, fake_sqlite_database, fake_mysql_database, mysql_credentials, faker
    ):
        with pytest.raises(mysql.connector.Error) as excinfo:
            SQLite3toMySQL(
                sqlite_file=fake_sqlite_database,
                mysql_user=faker.first_name().lower(),
                mysql_password=faker.password(length=16),
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
            )
        assert "Access denied for user" in str(excinfo.value)

    @pytest.mark.init
    def test_unspecified_mysql_error(
        self, fake_sqlite_database, mysql_credentials, mocker, faker, caplog
    ):
        class FakeConnector:
            def __init__(self):
                self._database = None

            @property
            def database(self):
                return self._database

            @database.setter
            def database(self, value):
                self._database = value
                # raise a fake exception
                raise mysql.connector.Error(
                    msg=faker.sentence(nb_words=12, variable_nb_words=True),
                    errno=errorcode.ER_SERVER_TEST_MESSAGE,
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

        mocker.patch.object(mysql.connector, "connect", return_value=FakeConnector())
        with pytest.raises(mysql.connector.Error) as excinfo:
            caplog.set_level(logging.DEBUG)
            SQLite3toMySQL(
                sqlite_file=fake_sqlite_database,
                mysql_user=mysql_credentials.user,
                mysql_password=mysql_credentials.password,
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
                chunk=1000,
            )
            assert str(errorcode.ER_SERVER_TEST_MESSAGE) in str(excinfo.value)
            assert any(
                str(errorcode.ER_SERVER_TEST_MESSAGE) in message
                for message in caplog.messages
            )

    @pytest.mark.init
    def test_bad_mysql_connection(
        self, fake_sqlite_database, mysql_credentials, mocker
    ):
        FakeConnector = namedtuple("FakeConnector", ["is_connected"])
        mocker.patch.object(
            mysql.connector,
            "connect",
            return_value=FakeConnector(is_connected=lambda: False),
        )
        with pytest.raises(ConnectionError) as excinfo:
            SQLite3toMySQL(
                sqlite_file=fake_sqlite_database,
                mysql_user=mysql_credentials.user,
                mysql_password=mysql_credentials.password,
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
                chunk=1000,
            )
        assert "Unable to connect to MySQL" in str(excinfo.value)

    @pytest.mark.init
    def test_log_to_file(
        self,
        fake_sqlite_database,
        fake_mysql_database,
        mysql_credentials,
        faker,
        caplog,
        tmpdir,
    ):
        log_file = tmpdir.join("db.log")
        with pytest.raises(mysql.connector.Error):
            caplog.set_level(logging.DEBUG)
            SQLite3toMySQL(
                sqlite_file=fake_sqlite_database,
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
    @pytest.mark.parametrize("chunk", [None, 1000])
    def test_transfer_transfers_all_tables_in_sqlite_file(
        self,
        fake_sqlite_database,
        fake_mysql_database,
        mysql_credentials,
        helpers,
        capsys,
        caplog,
        chunk,
    ):
        proc = SQLite3toMySQL(
            sqlite_file=fake_sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            chunk=chunk,
        )
        caplog.set_level(logging.DEBUG)
        proc.transfer()
        assert all(
            message in [record.message for record in caplog.records]
            for message in {
                "Transferring table article_authors",
                "Transferring table article_images",
                "Transferring table article_tags",
                "Transferring table articles",
                "Transferring table authors",
                "Transferring table images",
                "Transferring table tags",
                "Done!",
            }
        )
        assert all(record.levelname == "INFO" for record in caplog.records)
        assert not any(record.levelname == "ERROR" for record in caplog.records)
        out, err = capsys.readouterr()
        assert "Done!" in out.splitlines()[-1]

        sqlite_engine = create_engine(
            "sqlite:///{database}".format(database=fake_sqlite_database)
        )
        sqlite_cnx = sqlite_engine.connect()
        sqlite_inspect = inspect(sqlite_engine)
        sqlite_tables = sqlite_inspect.get_table_names()
        mysql_engine = create_engine(
            "mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}".format(
                user=mysql_credentials.user,
                password=mysql_credentials.password,
                host=mysql_credentials.host,
                port=mysql_credentials.port,
                database=mysql_credentials.database,
            )
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
            sqlite_results.append(sqlite_result)

        for table_name in mysql_tables:
            mysql_table = Table(
                table_name, meta, autoload=True, autoload_with=mysql_engine
            )
            mysql_stmt = select([mysql_table])
            mysql_result = mysql_cnx.execute(mysql_stmt).fetchall()
            mysql_result.sort()
            mysql_results.append(mysql_result)

        assert sqlite_results == mysql_results
