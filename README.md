[![PyPI](https://img.shields.io/pypi/v/sqlite3-to-mysql)](https://pypi.org/project/sqlite3-to-mysql/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/sqlite3-to-mysql)](https://pypistats.org/packages/sqlite3-to-mysql)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sqlite3-to-mysql)](https://pypi.org/project/sqlite3-to-mysql/)
[![MySQL Support](https://img.shields.io/static/v1?label=MySQL&message=5.5+|+5.6+|+5.7+|+8.0+|+8.4&color=2b5d80)](https://img.shields.io/static/v1?label=MySQL&message=5.5+|+5.6+|+5.7+|+8.0+|+8.4&color=2b5d80)
[![MariaDB Support](https://img.shields.io/static/v1?label=MariaDB&message=5.5+|+10.0+|+10.1+|+10.2+|+10.3+|+10.4+|+10.5+|+10.6|+10.11+|+11.4&color=C0765A)](https://img.shields.io/static/v1?label=MariaDB&message=5.5|+10.0+|+10.1+|+10.2+|+10.3+|+10.4+|+10.5|+11.4&color=C0765A)
[![GitHub license](https://img.shields.io/github/license/techouse/sqlite3-to-mysql)](https://github.com/techouse/sqlite3-to-mysql/blob/master/LICENSE)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE-OF-CONDUCT.md)
[![PyPI - Format](https://img.shields.io/pypi/format/sqlite3-to-mysql)]((https://pypi.org/project/sqlite3-to-mysql/))
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/d33b59d35b924711aae9418741a923ae)](https://www.codacy.com/manual/techouse/sqlite3-to-mysql?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=techouse/sqlite3-to-mysql&amp;utm_campaign=Badge_Grade)
[![Test Status](https://github.com/techouse/sqlite3-to-mysql/actions/workflows/test.yml/badge.svg)](https://github.com/techouse/sqlite3-to-mysql/actions/workflows/test.yml)
[![CodeQL Status](https://github.com/techouse/sqlite3-to-mysql/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/techouse/sqlite3-to-mysql/actions/workflows/codeql-analysis.yml)
[![Publish PyPI Package Status](https://github.com/techouse/sqlite3-to-mysql/actions/workflows/publish.yml/badge.svg)](https://github.com/techouse/sqlite3-to-mysql/actions/workflows/publish.yml)
[![Publish Docker Image](https://github.com/techouse/sqlite3-to-mysql/actions/workflows/docker.yml/badge.svg)](https://github.com/techouse/sqlite3-to-mysql/actions/workflows/docker.yml)
[![codecov](https://codecov.io/gh/techouse/sqlite3-to-mysql/branch/master/graph/badge.svg)](https://codecov.io/gh/techouse/sqlite3-to-mysql)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/techouse)](https://github.com/sponsors/techouse)
[![GitHub stars](https://img.shields.io/github/stars/techouse/sqlite3-to-mysql.svg?style=social&label=Star&maxAge=2592000)](https://github.com/techouse/sqlite3-to-mysql/stargazers)

# SQLite3 to MySQL

#### A simple Python tool to transfer data from SQLite 3 to MySQL.

### How to run

```bash
pip install sqlite3-to-mysql
sqlite3mysql --help
```

### Usage

```
Usage: sqlite3mysql [OPTIONS]

Options:
  -f, --sqlite-file PATH          SQLite3 database file  [required]
  -t, --sqlite-tables TUPLE       Transfer only these specific tables (space
                                  separated table names). Implies --without-
                                  foreign-keys which inhibits the transfer of
                                  foreign keys.
  -X, --without-foreign-keys      Do not transfer foreign keys.
  -W, --ignore-duplicate-keys     Ignore duplicate keys. The default behavior
                                  is to create new ones with a numerical
                                  suffix, e.g. 'exising_key' ->
                                  'existing_key_1'
  -d, --mysql-database TEXT       MySQL database name  [required]
  -u, --mysql-user TEXT           MySQL user  [required]
  -p, --prompt-mysql-password     Prompt for MySQL password
  --mysql-password TEXT           MySQL password
  -h, --mysql-host TEXT           MySQL host. Defaults to localhost.
  -P, --mysql-port INTEGER        MySQL port. Defaults to 3306.
  -S, --skip-ssl                  Disable MySQL connection encryption.
  -i, --mysql-insert-method [DEFAULT|IGNORE|UPDATE]
                                  MySQL insert method. DEFAULT will throw
                                  errors when encountering duplicate records;
                                  UPDATE will update existing rows; IGNORE
                                  will ignore insert errors. Defaults to
                                  IGNORE.
  -E, --mysql-truncate-tables     Truncates existing tables before inserting
                                  data.
  --mysql-integer-type TEXT       MySQL default integer field type. Defaults
                                  to INT(11).
  --mysql-string-type TEXT        MySQL default string field type. Defaults to
                                  VARCHAR(255).
  --mysql-text-type [LONGTEXT|MEDIUMTEXT|TEXT|TINYTEXT]
                                  MySQL default text field type. Defaults to
                                  TEXT.
  --mysql-charset TEXT            MySQL database and table character set
                                  [default: utf8mb4]
  --mysql-collation TEXT          MySQL database and table collation
  -T, --use-fulltext              Use FULLTEXT indexes on TEXT columns. Will
                                  throw an error if your MySQL version does
                                  not support InnoDB FULLTEXT indexes!
  --with-rowid                    Transfer rowid columns.
  -c, --chunk INTEGER             Chunk reading/writing SQL records
  -K, --mysql-skip-create-tables  Skip creating tables in MySQL.
  -J, --mysql-skip-transfer-data  Skip transferring data to MySQL.
  -l, --log-file PATH             Log file
  -q, --quiet                     Quiet. Display only errors.
  --debug                         Debug mode. Will throw exceptions.
  --version                       Show the version and exit.
  --help                          Show this message and exit.
```

#### Docker

If you don't want to install the tool on your system, you can use the Docker image instead.

```bash
docker run -it \
    --workdir $(pwd) \
    --volume $(pwd):$(pwd) \
    --rm ghcr.io/techouse/sqlite3-to-mysql:latest \
    --sqlite-file baz.db \
    --mysql-user foo \
    --mysql-password bar \
    --mysql-database baz \
    --mysql-host host.docker.internal
```

This will mount your host current working directory (pwd) inside the Docker container as the current working directory.
Any files Docker would write to the current working directory are written to the host directory where you did docker
run. Note that you have to also use a
[special hostname](https://docs.docker.com/desktop/networking/#use-cases-and-workarounds-for-all-platforms)
`host.docker.internal`
to access your host machine from inside the Docker container.

#### Homebrew

If you're on macOS, you can install the tool using [Homebrew](https://brew.sh/).

```bash
brew tap techouse/sqlite3-to-mysql
brew install sqlite3-to-mysql
sqlite3mysql --help
```
