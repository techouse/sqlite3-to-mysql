import pytest

from sqlalchemy.dialects.sqlite import __all__ as sqlite_column_types

from src.sqlite3_to_mysql import SQLite3toMySQL


class TestSQLite3toMySQL:
    def test_translate_type_from_sqlite_to_mysql_invalid_column_type(self, mocker):
        mocker.patch.object(SQLite3toMySQL, "_valid_column_type", return_value=False)
        with pytest.raises(ValueError) as excinfo:
            SQLite3toMySQL._translate_type_from_sqlite_to_mysql("text")
        assert "Invalid column_type!" in str(excinfo.value)

    def test_translate_type_from_sqlite_to_mysql_all_valid_columns(self, faker):
        for column in sqlite_column_types:
            if column not in {"dialect", "VARCHAR"}:
                assert (
                    SQLite3toMySQL._translate_type_from_sqlite_to_mysql(column)
                    == column
                )
        assert SQLite3toMySQL._translate_type_from_sqlite_to_mysql("TEXT") == "TEXT"
        assert SQLite3toMySQL._translate_type_from_sqlite_to_mysql("CLOB") == "TEXT"
        assert (
            SQLite3toMySQL._translate_type_from_sqlite_to_mysql("CHARACTER") == "CHAR"
        )
        length = faker.pyint(min_value=1, max_value=99)
        assert SQLite3toMySQL._translate_type_from_sqlite_to_mysql(
            "CHARACTER({})".format(length)
        ) == "CHAR({})".format(length)
        assert SQLite3toMySQL._translate_type_from_sqlite_to_mysql("NCHAR") == "CHAR"
        length = faker.pyint(min_value=1, max_value=99)
        assert SQLite3toMySQL._translate_type_from_sqlite_to_mysql(
            "NCHAR({})".format(length)
        ) == "CHAR({})".format(length)
        assert (
            SQLite3toMySQL._translate_type_from_sqlite_to_mysql("NATIVE CHARACTER")
            == "CHAR"
        )
        length = faker.pyint(min_value=1, max_value=99)
        assert SQLite3toMySQL._translate_type_from_sqlite_to_mysql(
            "NATIVE CHARACTER({})".format(length)
        ) == "CHAR({})".format(length)
        assert (
            SQLite3toMySQL._translate_type_from_sqlite_to_mysql("VARCHAR")
            == "VARCHAR(255)"
        )
        length = faker.pyint(min_value=1, max_value=255)
        assert SQLite3toMySQL._translate_type_from_sqlite_to_mysql(
            "VARCHAR({})".format(length)
        ) == "VARCHAR({})".format(length)
        assert (
            SQLite3toMySQL._translate_type_from_sqlite_to_mysql("DOUBLE PRECISION")
            == "DOUBLE"
        )
        assert (
            SQLite3toMySQL._translate_type_from_sqlite_to_mysql("UNSIGNED BIG INT")
            == "BIGINT UNSIGNED"
        )
        length = faker.pyint(min_value=1000000000, max_value=99999999999999999999)
        assert SQLite3toMySQL._translate_type_from_sqlite_to_mysql(
            "UNSIGNED BIG INT({})".format(length)
        ) == "BIGINT({}) UNSIGNED".format(length)
        assert SQLite3toMySQL._translate_type_from_sqlite_to_mysql("INT1") == "INT"
        assert SQLite3toMySQL._translate_type_from_sqlite_to_mysql("INT2") == "INT"
