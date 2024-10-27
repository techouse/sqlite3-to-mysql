# 2.3.2

* [FIX] fix --mysql-insert-method
* [FIX] modify the existing `check_mysql_json_support` and `check_mysql_fulltext_support` to improve detection of
  MariaDB versions
* [FIX] fix connecting with empty MySQL password

# 2.3.1

* [FIX] fix conversion of SQLite `NUMERIC` data type with precision and scale to MySQL `DECIMAL` with precision and
  scale

# 2.3.0

* [FEAT] add MySQL 8.4 and MariaDB 11.4 support

# 2.2.1

* [FIX] use `dateutil.parse` to parse SQLite dates

# 2.2.0

* [FEAT] add `--mysql-skip-create-tables` and `--mysql-skip-transfer-data` options
* [FIX] fix default parameter parsing
* [CHORE] update Sphinx documentation

# 2.1.10

* [CHORE] add Sphinx documentation

# 2.1.9

* [FEAT] add conversion of SQLite custom `BOOL` data type to MySQL `TINYINT(1)`

# 2.1.8

* [CHORE] migrate package from flat layout to src layout

# 2.1.7

* [FEAT] add copyright header

# 2.1.6

* [FEAT] build both linux/amd64 and linux/arm64 Docker images

# 2.1.5

* [FEAT] add support for UNSIGNED numeric data type conversion
* [FIX] fix invalid column_type error message

# 2.1.4

* [CHORE] maintenance release to publish first containerized release

# 2.1.3

* [FIX] add packaging as a dependency

# 2.1.2

* [FIX] throw more comprehensive error messages when translating column types

# 2.1.1

* [CHORE] add support for Python 3.12
* [CHORE] bump minimum version of MySQL Connector/Python to 8.2.0

# 2.1.0

* [CHORE] drop support for Python 3.7

# 2.0.3

* [FIX] prevent AUTO_INCREMENT-ing fields from having a DEFAULT value

# 2.0.2

* [FIX] properly import CMySQLConnection

# 2.0.1

* [FIX] fix types

# 2.0.0

* [CHORE] drop support for Python 2.7, 3.5 and 3.6
* [CHORE] migrate pytest.ini configuration into pyproject.toml
* [CHORE] migrate from setuptools to hatch / hatchling
* [CHORE] add types
* [CHORE] add types to tests
* [CHORE] update dependencies
* [CHORE] use f-strings where appropriate

# 1.4.20

* [CHORE] update dependencies
* [CHORE] use [black](https://github.com/psf/black) and [isort](https://github.com/PyCQA/isort) in tox linters

# 1.4.19

* [FEAT] handle generated columns

# 1.4.18

* [CHORE] migrate from setup.py to pyproject.toml

# 1.4.17

* [CHORE] add publishing workflow
* [CHORE] add Python 3.11 support
* [CHORE] Remove CI tests for Python 3.5, 3.6, add CI tests for Python 3.11
* [CHORE] add MariaDB 10.11 CI tests

# 1.4.16

* [FIX] pin mysql-connector-python to <8.0.30
* [CHORE] update CI actions/checkout to v3
* [CHORE] update CI actions/setup-python to v4
* [CHORE] update CI actions/cache to v3
* [CHORE] update CI github/codeql-action/init to v2
* [CHORE] update CI github/codeql-action/analyze to v2
* [CHORE] update CI codecov/codecov-action to v2

# 1.4.15

* [FEAT] add option to truncate existing tables before inserting data

# 1.4.14

* [FIX] fix safe_identifier_length

# 1.4.13

* [FEAT] add option to update duplicate records
* [FEAT] add option to skip duplicate index creation if key name already exists
* [CHORE] mark test_quiet with xfail
* [CHORE] fix CLI test
* [CHORE] remove Fix MySQL GA Github Action step

# 1.4.12

* [FEAT] add --debug switch
* [FIX] import backports-datetime-fromisoformat only for Python 3.4, 3.5 and 3.6
* [FIX] handle SQLite date conversion

# 1.4.11

* [FIX] fix regression introduced in v1.4.9

# 1.4.10

* [FEAT] add ability to change default text type using --mysql-text-type
* [FIX] fix BOOLEAN conversion to TINYINT(1)

# 1.4.9

* [FEAT] add support for DEFAULT statements

# 1.4.8

* [CHORE] fix tests

# 1.4.7

* [CHORE] add support for Python 3.10
* [CHORE] add Python 3.10 tests

# 1.4.6

* [FEAT] add CLI options for custom charset and collation
* [FEAT] add unicase custom collation
* [FIX] limit MySQL identifier to 64 characters
* [FIX] handle multiple column FULLTEXT index transfer error
* [FIX] fix multiple column index length #28
* [CHORE] move some MySQL helper methods out of the main transporter
* [CHORE] refactor package
* [CHORE] add experimental tests for Python 3.10-dev

# 1.4.5

* [FIX] revert change introduced in v1.4.4
* [FIX] fix Click 8.0 OptionEatAll wrong type
* [CHORE] add tests for MariaDB 10.6

# 1.4.4

* [FIX] pin Click to <8.0

# 1.4.3

* [FIX] pin python-tabulate to <0.8.6 for Python 3.4 or less
* [FIX] pin Click to <8.0 only for Python 3.5 or less

# 1.4.2

* [FIX] fix auto_increment
* [CHORE] add DECIMAL test
* [FIX] pin Click to <8.0

# 1.4.1

* [FIX] pin mysql-connector-python to <8.0.24 for Python 3.5 or lower

# 1.4.0

* [FEAT] add password prompt. This changes the default behavior of -p
* [FEAT] add option to disable MySQL connection encryption
* [FEAT] add progress bar
* [FEAT] implement feature to transport custom data types as strings
* [FIX] require sqlalchemy <1.4.0 to make compatible with sqlalchemy-utils
* [CHORE] fix CI tests

# 1.3.12

* [FIX] handle duplicate indices
* [CHORE] transition from Travis CI to GitHub Actions

# 1.3.11

* [CHORE] add Python 3.9 tests

# 1.3.10

* [FEAT] add --use-fulltext option
* [FIX] use FULLTEXT index only if all columns are TEXT

# 1.3.9

* [FEAT] add --quiet option

# 1.3.8

* [FIX] test for mysql client more gracefully

# 1.3.7

* [FEAT] transfer composite primary keys

# 1.3.6

* [FEAT] simpler access to the debug version info using the --version switch
* [FEAT] add debug_info module to be used in bug reports
* [CHORE] use pytest fixture fom Faker 4.1.0 in Python 3 tests
* [CHORE] omit debug_info.py in coverage reports

# 1.3.5

* [FEAT] set default collation of newly created databases and tables to utf8mb4_general_ci
* [FEAT] optional transfer of implicit column rowid using --with-rowid
* [CHORE] test non-numeric primary keys
* [CHORE] add rowid transfer tests
* [CHORE] fix tests

# 1.3.4

* [FIX] fix information_schema issue introduced with MySQL 8.0.21
* [FIX] sqlalchemy-utils dropped Python 2.7 support in v0.36.7
* [CHORE] add MySQL version output to CI tests
* [CHORE] add Python 3.9 to the CI tests
* [CHORE] add MariaDB 10.5 to the CI tests
* [CHORE] remove Python 2.7 from allowed CI test failures
* [CHORE] use Ubuntu Bionic instead of Ubuntu Xenial in CI tests

# 1.3.3

* [FEAT] add support for SQLite STRING and translate it as MySQL TEXT

# 1.3.2

* [FIX] force not null on primary-key columns

# 1.3.1

* [CHORE] test legacy databases in CI tests
* [CHORE] fix MySQL 8 CI tests

# 1.3.0

* [FEAT] add option to transfer only specific tables using -t
* [CHORE] add tests for transferring only certain tables

# 1.2.17

* [FIX] properly escape foreign keys names

# 1.2.16

* [FIX] differentiate better between MySQL and SQLite errors
* [CHORE] add Python 3.8 and 3.8-dev test build

# 1.2.15

* [CHORE] update Readme on PyPI

# 1.2.14

* [FIX] add INT64 as an alias for NUMERIC
* [CHORE] add support for Python 3.8
* [CHORE] add INT64 tests

# 1.2.13

* [CHORE] add [bandit](https://github.com/PyCQA/bandit) tests
* [CHORE] add more tests to increase test coverage
* [CHORE] fix tests

# 1.2.12

* [FEAT] transfer indices
* [CHORE] add additional index transfer tests

# 1.2.11

* [FIX] remove redundant SQL cleanup
* [CHORE] clean up a test

# 1.2.10

* [CHORE] update development requirements

# 1.2.9

* [FIX] change the way foreign keys are added.
* [FIX] change default MySQL character set to utf8mb4
* [CHORE] add more verbosity

# 1.2.8

* [FIX] disable FOREIGN_KEY_CHECKS before inserting the foreign keys and enable FOREIGN_KEY_CHECKS back once finished

# 1.2.7

* [FEAT] transfer foreign keys
* [FIX] in Python 2 MySQL binary protocol can not handle 'buffer' objects so we have to convert them to strings
* [CHORE] test transfer of foreign keys
* [CHORE] only test databases that support JSON
* [CHORE] fix tests

# 1.2.6

* [CHORE] refactor package

# 1.2.5

* [CHORE] update Readme

# 1.2.4

* [CHORE] fix CI tests
* [CHORE] add linter rules

# 1.2.3

* [CHORE] refactor package
* [CHORE] test the CLI interface
* [CHORE] fix tests

# 1.2.2

* [FEAT] add Python 2.7 support
* [CHORE] refactor package
* [CHORE] fix tests
* [CHORE] add option to test against a real SQLite file

# 1.2.1

* [FIX] catch exceptions
* [FIX] default mysql_string_type from VARCHAR(300) to VARCHAR(255)
* [CHORE] fix CI tests
* [CHORE] option to run tests against a physical MySQL server instance as well as a Docker one
* [CHORE] run tests against any Docker image with a MySQL/MariaDB database
* [CHORE] clean up hanged Docker images with the name "pytest_sqlite3_to_mysql"
* [CHORE] 100% code coverage

# 1.2.0

* [CHORE] add more tests

# 1.1.2

* [FIX] fix creation of tables with non-numeric primary keys

# 1.1.1

* [FIX] fix error of transferring empty tables

# 1.1.0

* [CHORE] update to work with MySQL Connector/Python v8.0.11+

# 1.0.3

* [FIX] don't autoincrement if primary key is TEXT/VARCHAR

# 1.0.2

* [CHORE] refactor package

# 1.0.1

* [CHORE] change license from GPL to MIT

# 1.0.0

Initial commit