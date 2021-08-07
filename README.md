[![PyPI](https://img.shields.io/pypi/v/sqlite3-to-mysql)](https://pypi.org/project/sqlite3-to-mysql/)
[![Downloads](https://pepy.tech/badge/sqlite3-to-mysql)](https://pepy.tech/project/sqlite3-to-mysql)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sqlite3-to-mysql)](https://pypi.org/project/sqlite3-to-mysql/)
[![MySQL Support](https://img.shields.io/static/v1?label=MySQL&message=5.5+|+5.6+|+5.7+|+8.0&color=2b5d80)](https://img.shields.io/static/v1?label=MySQL&message=5.6+|+5.7+|+8.0&color=2b5d80)
[![MariaDB Support](https://img.shields.io/static/v1?label=MariaDB&message=5.5+|+10.0+|+10.1+|+10.2+|+10.3+|+10.4+|+10.5+|+10.6&color=C0765A)](https://img.shields.io/static/v1?label=MariaDB&message=10.0+|+10.1+|+10.2+|+10.3+|+10.4+|+10.5&color=C0765A)
[![GitHub license](https://img.shields.io/github/license/techouse/sqlite3-to-mysql)](https://github.com/techouse/sqlite3-to-mysql/blob/master/LICENSE)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.0-4baaaa.svg)](CODE-OF-CONDUCT.md)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/d33b59d35b924711aae9418741a923ae)](https://www.codacy.com/manual/techouse/sqlite3-to-mysql?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=techouse/sqlite3-to-mysql&amp;utm_campaign=Badge_Grade)
[![Build Status](https://github.com/techouse/sqlite3-to-mysql/workflows/Test/badge.svg)](https://github.com/techouse/sqlite3-to-mysql/actions?query=workflow%3ATest)
[![codecov](https://codecov.io/gh/techouse/sqlite3-to-mysql/branch/master/graph/badge.svg)](https://codecov.io/gh/techouse/sqlite3-to-mysql)
[![GitHub stars](https://img.shields.io/github/stars/techouse/sqlite3-to-mysql.svg?style=social&label=Star&maxAge=2592000)](https://github.com/techouse/sqlite3-to-mysql/stargazers)


# SQLite3 to MySQL

#### A simple Python tool to transfer data from SQLite 3 to MySQL.

I originally wrote this simple program as a standalone script and published it
as a [gist](https://gist.github.com/techouse/4deb94eee58a02d104c6) as an answer
to this [Stack Overflow question](https://stackoverflow.com/questions/18671/quick-easy-way-to-migrate-sqlite3-to-mysql/32243979#32243979).
Since then quite some people have taken interest in it since it's so simple and
effective. Therefore I finally moved my lazy bones and made a GitHub repository :octopus:.

### How to run

```bash
pip install sqlite3-to-mysql
sqlite3mysql --help
```

### Usage
```
Usage: sqlite3mysql [OPTIONS]

  Transfer SQLite to MySQL using the provided CLI options.

Options:
  -f, --sqlite-file PATH       SQLite3 database file  [required]
  -t, --sqlite-tables TEXT     Transfer only these specific tables (space
                               separated table names). Implies --without-
                               foreign-keys which inhibits the transfer of
                               foreign keys.

  -X, --without-foreign-keys   Do not transfer foreign keys.
  -d, --mysql-database TEXT    MySQL database name  [required]
  -u, --mysql-user TEXT        MySQL user  [required]
  -p, --prompt-mysql-password  Prompt for MySQL password
  --mysql-password TEXT        MySQL password
  -h, --mysql-host TEXT        MySQL host. Defaults to localhost.
  -P, --mysql-port INTEGER     MySQL port. Defaults to 3306.
  -S, --skip-ssl               Disable MySQL connection encryption.
  --mysql-integer-type TEXT    MySQL default integer field type. Defaults to
                               INT(11).

  --mysql-string-type TEXT     MySQL default string field type. Defaults to
                               VARCHAR(255).

  -T, --use-fulltext           Use FULLTEXT indexes on TEXT columns. Will
                               throw an error if your MySQL version does not
                               support InnoDB FULLTEXT indexes!

  --with-rowid                 Transfer rowid columns.
  -c, --chunk INTEGER          Chunk reading/writing SQL records
  -l, --log-file PATH          Log file
  -q, --quiet                  Quiet. Display only errors.
  --version                    Show the version and exit.
  --help                       Show this message and exit.
```
