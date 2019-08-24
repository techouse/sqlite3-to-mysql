import re

import pytest

from sqlalchemy.dialects.sqlite import __all__ as sqlite_column_types

from src.sqlite3_to_mysql import SQLite3toMySQL


@pytest.mark.usefixtures("fake_sqlite_database", "docker_mysql")
class TestSQLite3toMySQL:
    def test_translate_type_from_sqlite_to_mysql_invalid_column_type(
        self, fake_sqlite_database, fake_mysql_database, mysql_credentials, mocker
    ):
        with pytest.raises(ValueError) as excinfo:
            proc = SQLite3toMySQL(
                sqlite_file=fake_sqlite_database,
                mysql_user=mysql_credentials.user,
                mysql_password=mysql_credentials.password,
                mysql_host=mysql_credentials.host,
                mysql_port=mysql_credentials.port,
                mysql_database=mysql_credentials.database,
            )
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
        fake_sqlite_database,
        fake_mysql_database,
        mysql_credentials,
        faker,
        mysql_integer_type,
        mysql_string_type,
    ):
        proc = SQLite3toMySQL(
            sqlite_file=fake_sqlite_database,
            mysql_user=mysql_credentials.user,
            mysql_password=mysql_credentials.password,
            mysql_host=mysql_credentials.host,
            mysql_port=mysql_credentials.port,
            mysql_database=mysql_credentials.database,
            mysql_integer_type=mysql_integer_type,
            mysql_string_type=mysql_string_type,
        )

        for column in sqlite_column_types:
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
            elif column == "NUMERIC":
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
