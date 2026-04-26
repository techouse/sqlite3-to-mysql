[![PyPI](https://img.shields.io/pypi/v/sqlite3-to-mysql?logo=pypi)](https://pypi.org/project/sqlite3-to-mysql/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/sqlite3-to-mysql?logo=pypi&label=PyPI%20downloads)](https://pypistats.org/packages/sqlite3-to-mysql)
[![Homebrew Formula Downloads](https://img.shields.io/homebrew/installs/dm/sqlite3-to-mysql?logo=homebrew&label=Homebrew%20downloads)](https://formulae.brew.sh/formula/sqlite3-to-mysql)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sqlite3-to-mysql?logo=python)](https://pypi.org/project/sqlite3-to-mysql/)
[![MySQL Support](https://img.shields.io/static/v1?logo=mysql&label=MySQL&message=5.5+|+5.6+|+5.7+|+8.0+|+8.4&color=2b5d80)](https://img.shields.io/static/v1?label=MySQL&message=5.5+|+5.6+|+5.7+|+8.0+|+8.4&color=2b5d80)
[![MariaDB Support](https://img.shields.io/static/v1?logo=mariadb&label=MariaDB&message=5.5+|+10.0+|+10.6+|+10.11+|+11.4+|+11.6+|+11.8&color=C0765A)](https://img.shields.io/static/v1?label=MariaDB&message=5.5+|+10.0+|+10.6+|+10.11+|+11.4+|+11.6+|+11.8&color=C0765A)
[![GitHub license](https://img.shields.io/github/license/techouse/sqlite3-to-mysql)](https://github.com/techouse/sqlite3-to-mysql/blob/master/LICENSE)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg?logo=contributorcovenant)](CODE-OF-CONDUCT.md)
[![PyPI - Format](https://img.shields.io/pypi/format/sqlite3-to-mysql?logo=python)](https://pypi.org/project/sqlite3-to-mysql/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?logo=python)](https://github.com/ambv/black)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/d33b59d35b924711aae9418741a923ae)](https://www.codacy.com/manual/techouse/sqlite3-to-mysql?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=techouse/sqlite3-to-mysql&amp;utm_campaign=Badge_Grade)
[![Test Status](https://github.com/techouse/sqlite3-to-mysql/actions/workflows/test.yml/badge.svg)](https://github.com/techouse/sqlite3-to-mysql/actions/workflows/test.yml)
[![CodeQL Status](https://github.com/techouse/sqlite3-to-mysql/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/techouse/sqlite3-to-mysql/actions/workflows/github-code-scanning/codeql)
[![Publish PyPI Package Status](https://github.com/techouse/sqlite3-to-mysql/actions/workflows/publish.yml/badge.svg)](https://github.com/techouse/sqlite3-to-mysql/actions/workflows/publish.yml)
[![codecov](https://codecov.io/gh/techouse/sqlite3-to-mysql/branch/master/graph/badge.svg)](https://codecov.io/gh/techouse/sqlite3-to-mysql)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/techouse?logo=github)](https://github.com/sponsors/techouse)
[![GitHub stars](https://img.shields.io/github/stars/techouse/sqlite3-to-mysql.svg?style=social&label=Star&maxAge=2592000)](https://github.com/techouse/sqlite3-to-mysql/stargazers)

# SQLite3 to MySQL

A Python command-line tool for transferring schema, indexes, foreign keys, views, and data from SQLite 3 to MySQL or
MariaDB.

## Installation

```bash
pip install sqlite3-to-mysql
```

On macOS, you can also use Homebrew:

```bash
brew install sqlite3-to-mysql
```

## Requirements

- Python 3.9 or newer.
- A readable SQLite 3 database file.
- A reachable MySQL or MariaDB server.
- A MySQL user that can connect, create the target database when it does not exist, create tables and views, insert data,
  add indexes, and add foreign keys.

## Quick Start

Transfer an SQLite database to a MySQL database using an interactive password prompt:

```bash
sqlite3mysql \
    --sqlite-file path/to/app.sqlite3 \
    --mysql-database app_db \
    --mysql-user app_user \
    --prompt-mysql-password
```

For the complete option reference, run:

```bash
sqlite3mysql --help
```

## Common Workflows

Connect to a non-default host or port:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p -h 127.0.0.1 -P 3307
```

Pass the password directly when a prompt is not practical:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user --mysql-password "$MYSQL_PASSWORD"
```

Transfer only selected tables:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p --sqlite-tables users posts comments
```

Transfer everything except selected tables:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p --exclude-sqlite-tables audit_logs cache_entries
```

Create tables without copying data:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p --mysql-skip-transfer-data
```

Copy data into tables that already exist:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p --mysql-skip-create-tables
```

Truncate matching target tables before inserting data:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p --mysql-truncate-tables
```

Update existing rows when inserts hit duplicate keys:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p --mysql-insert-method UPDATE
```

Use a Unix socket:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p --mysql-socket /var/run/mysqld/mysqld.sock
```

Use TLS with a CA certificate:

```bash
sqlite3mysql \
    -f app.sqlite3 \
    -d app_db \
    -u app_user \
    -p \
    --mysql-ssl-ca /path/to/ca.pem
```

Use client certificate authentication:

```bash
sqlite3mysql \
    -f app.sqlite3 \
    -d app_db \
    -u app_user \
    -p \
    --mysql-ssl-ca /path/to/ca.pem \
    --mysql-ssl-cert /path/to/client-cert.pem \
    --mysql-ssl-key /path/to/client-key.pem
```

Write logs to a file and suppress progress output:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p --quiet --log-file transfer.log
```

## Behavior Notes

- The target database is created automatically when it does not exist.
- Tables are created with `CREATE TABLE IF NOT EXISTS`, so matching target tables are kept.
- `--mysql-truncate-tables` truncates matching target tables before data is inserted.
- The default insert mode is `IGNORE`. Use `DEFAULT` to let duplicate records fail, or `UPDATE` to update existing rows
  on duplicate keys.
- Native MySQL views are created by default. If a target table has the same name as a SQLite view, that target table is
  dropped before the MySQL view is created. Use `--sqlite-views-as-tables` to materialize SQLite views as MySQL tables.
- `--with-rowid` adds an explicit `rowid` column only for SQLite tables that have a rowid.
- Table, view, column, index, and constraint names are truncated to MySQL's 64-character identifier limit.
- Foreign key checks are disabled during transfer and re-enabled before the command exits.
- If MySQL rejects a table because of invalid default values, the table creation is retried without default values.

## Option Caveats

- `--sqlite-tables` and `--exclude-sqlite-tables` are mutually exclusive.
- Either table filter implies `--without-foreign-keys`, because partial transfers cannot safely recreate all foreign key
  relationships.
- `--mysql-skip-create-tables` and `--mysql-skip-transfer-data` cannot be used together.
- `--mysql-socket` cannot be combined with `--mysql-ssl-ca`, `--mysql-ssl-cert`, or `--mysql-ssl-key`.
- `--skip-ssl` cannot be combined with `--mysql-ssl-ca`, `--mysql-ssl-cert`, or `--mysql-ssl-key`.
- `--mysql-ssl-cert` and `--mysql-ssl-key` must be provided together.
- `--mysql-collation` must be valid for the selected `--mysql-charset`.
- `--use-fulltext` requires a target server with InnoDB FULLTEXT support. If the server does not support it, the command
  fails before transfer starts.

MySQL SSL note: when `--mysql-ssl-ca` is provided, MySQL Connector/Python verifies the server certificate chain.
`--mysql-ssl-cert` and `--mysql-ssl-key` enable client certificate authentication. These options do not enable hostname
identity verification. If you provide only the client certificate and key without `--mysql-ssl-ca`, the server
certificate is not verified.

## MySQL and MariaDB Compatibility

MariaDB began as a MySQL fork, but server capabilities and SQL syntax have diverged. The transfer logic checks the server
version and adjusts behavior for several features:

| Feature | MySQL | MariaDB | Notes |
| --- | --- | --- | --- |
| JSON support | `>= 5.7.8` | `>= 10.2.7` | SQLite `JSONB` maps to `JSON` when supported, otherwise to the configured text type. |
| `UPDATE` insert alias | `>= 8.0.19` | Not used | MariaDB keeps the older duplicate-key update form. |
| Expression defaults | `>= 8.0.13` | `>= 10.2.0` | Older servers may require defaults to be omitted or simplified. |
| `CURRENT_TIMESTAMP` for `DATETIME` | `>= 5.6.5` | `>= 10.0.1` | Older servers cannot use this default on `DATETIME`. |
| Fractional seconds | `>= 5.6.4` | `>= 10.1.2` | Fractional precision is preserved only when supported. |
| InnoDB FULLTEXT indexes | `>= 5.6.0` | `>= 10.0.5` | Required for `--use-fulltext`. |

SQLite `JSONB` value conversion requires SQLite 3.45 or newer. With older SQLite versions, JSONB columns can still be
selected, but the SQLite `json()` conversion function is not used during transfer.

## Docker

If you do not want to install the tool on your system, use the Docker image:

```bash
docker run -it \
    --workdir "$(pwd)" \
    --volume "$(pwd):$(pwd)" \
    --rm ghcr.io/techouse/sqlite3-to-mysql:latest \
    --sqlite-file app.sqlite3 \
    --mysql-user app_user \
    --mysql-password "$MYSQL_PASSWORD" \
    --mysql-database app_db \
    --mysql-host host.docker.internal
```

This mounts the current host directory into the container as the working directory. On Docker Desktop,
`host.docker.internal` lets the container connect back to a MySQL server running on the host.

## Documentation

- [Full documentation](https://techouse.github.io/sqlite3-to-mysql/)
- [Changelog](CHANGELOG.md)
- [Issue tracker](https://github.com/techouse/sqlite3-to-mysql/issues)

## License

SQLite3 to MySQL is released under the [MIT License](LICENSE).
