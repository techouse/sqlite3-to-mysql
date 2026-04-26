[![PyPI](https://img.shields.io/pypi/v/sqlite3-to-mysql?logo=pypi)](https://pypi.org/project/sqlite3-to-mysql/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/sqlite3-to-mysql?logo=pypi&label=PyPI%20downloads)](https://pypistats.org/packages/sqlite3-to-mysql)
[![Homebrew Formula Downloads](https://img.shields.io/homebrew/installs/dm/sqlite3-to-mysql?logo=homebrew&label=Homebrew%20downloads)](https://formulae.brew.sh/formula/sqlite3-to-mysql)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sqlite3-to-mysql?logo=python)](https://pypi.org/project/sqlite3-to-mysql/)
[![MySQL Support](https://img.shields.io/static/v1?logo=mysql&label=MySQL&message=5.5+|+5.6+|+5.7+|+8.0+|+8.4&color=2b5d80)](https://github.com/techouse/sqlite3-to-mysql/actions/workflows/test.yml)
[![MariaDB Support](https://img.shields.io/static/v1?logo=mariadb&label=MariaDB&message=5.5+|+10.0+|+10.6+|+10.11+|+11.4+|+11.6+|+11.8&color=C0765A)](https://github.com/techouse/sqlite3-to-mysql/actions/workflows/test.yml)
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

A Python CLI for transferring SQLite 3 schema and data to MySQL or MariaDB.

`sqlite3mysql` reads the source schema from SQLite, creates equivalent MySQL/MariaDB tables, indexes, foreign keys, and
views where possible, then transfers table data into the target database.

## Prerequisites

- Python 3.9 or newer, unless you use the Docker image.
- A readable SQLite 3 database file.
- A reachable MySQL or MariaDB server.
- A MySQL user that can connect, create the target database when it does not exist, create tables and views, insert data,
  add indexes, and add foreign keys.

See the
[GitHub Actions CI matrix](https://github.com/techouse/sqlite3-to-mysql/blob/master/.github/workflows/test.yml) for the
current MySQL and MariaDB versions tested by the project. Very old server versions are more likely to differ in type,
default-value, JSON, FULLTEXT, or authentication behavior.

## Installation

Install from PyPI:

```bash
pip install sqlite3-to-mysql
sqlite3mysql --help
```

On macOS, you can also install with Homebrew:

```bash
brew install sqlite3-to-mysql
sqlite3mysql --help
```

Or run the published Docker image:

```bash
docker run --rm ghcr.io/techouse/sqlite3-to-mysql:latest --help
```

## Agent skill

This repo includes an optional agent skill at [`SKILL.md`](SKILL.md) for users who want Codex or another compatible agent
to help prepare a safe `sqlite3mysql` transfer command. The skill is user-facing: it focuses on migration planning, CLI
recipes, password-safe defaults, and MySQL/MariaDB caveats.

## Quick start

Use `-p` / `--prompt-mysql-password` for interactive password entry. This avoids putting the password in shell history
or process listings.

```bash
sqlite3mysql \
    --sqlite-file ./app.sqlite3 \
    --mysql-database app_db \
    --mysql-user app_user \
    --prompt-mysql-password \
    --mysql-host 127.0.0.1 \
    --mysql-port 3306
```

Short options are equivalent:

```bash
sqlite3mysql -f ./app.sqlite3 -d app_db -u app_user -p -h 127.0.0.1 -P 3306
```

For automation, `--mysql-password` is available, but prefer a secret manager or environment-expanded value rather than
typing the password directly into your shell history. The password is still passed as a command-line argument and may be
visible through process listings or logs.

## Common recipes

### Run with Docker

Use `host.docker.internal` when the MySQL or MariaDB server is running on the host machine and the Docker container needs
to reach it. On Linux Docker Engine, add `--add-host=host.docker.internal:host-gateway` before the image name if
`host.docker.internal` is not resolvable.

```bash
docker run -it \
    --rm \
    --workdir "$PWD" \
    --volume "$PWD:$PWD" \
    ghcr.io/techouse/sqlite3-to-mysql:latest \
    -f ./app.sqlite3 \
    -d app_db \
    -u app_user \
    -p \
    -h host.docker.internal
```

Files inside the mounted working directory are shared with the host.

### Transfer schema only

Create the MySQL tables, indexes, views, and foreign keys without transferring table rows.

```bash
sqlite3mysql -f ./schema.sqlite3 -d app_db -u app_user -p --mysql-skip-transfer-data
```

### Transfer data into existing MySQL tables

`--mysql-skip-create-tables` skips DDL creation and only inserts data. The MySQL tables must already exist and be
compatible with the SQLite source schema.

```bash
sqlite3mysql -f ./app.sqlite3 -d app_db -u app_user -p --mysql-skip-create-tables
```

### Transfer only some tables

Table names are space-separated and are consumed until the next CLI option.

```bash
sqlite3mysql -f ./subset.sqlite3 -d app_db -u app_user -p --sqlite-tables users orders invoices
```

Transfer everything except selected tables:

```bash
sqlite3mysql -f ./subset.sqlite3 -d app_db -u app_user -p --exclude-sqlite-tables audit_log temp_imports
```

Selecting or excluding tables disables foreign key transfer because the referenced tables may not be present.

### Refresh existing target tables

`--mysql-truncate-tables` deletes rows from matching target tables before inserting data.

```bash
sqlite3mysql -f ./app.sqlite3 -d app_db -u app_user -p --mysql-truncate-tables
```

Use `--mysql-insert-method UPDATE` to update existing rows when inserts hit duplicate keys.

```bash
sqlite3mysql -f ./app.sqlite3 -d app_db -u app_user -p --mysql-insert-method UPDATE
```

### Use a Unix socket

Use a socket instead of TCP when the MySQL server is local and configured for socket connections.

```bash
sqlite3mysql -f ./app.sqlite3 -d app_db -u app_user -p --mysql-socket /var/run/mysqld/mysqld.sock
```

### Use SSL certificates

Verify the server certificate with a CA file:

```bash
sqlite3mysql -f ./app.sqlite3 -d app_db -u app_user -p --mysql-ssl-ca /path/to/ca.pem
```

Use a client certificate and key:

```bash
sqlite3mysql \
    -f ./app.sqlite3 \
    -d app_db \
    -u app_user \
    -p \
    --mysql-ssl-ca /path/to/ca.pem \
    --mysql-ssl-cert /path/to/client-cert.pem \
    --mysql-ssl-key /path/to/client-key.pem
```

Use `--skip-ssl` only when you explicitly need to disable MySQL connection encryption.

### Tune large transfers and logs

Use `--chunk` to tune the number of SQLite rows read at a time. Use `--quiet` to suppress progress output and
`--log-file` to write logs to a file.

```bash
sqlite3mysql -f ./app.sqlite3 -d app_db -u app_user -p --chunk 50000 --quiet --log-file transfer.log
```

## Options at a glance

| Option | Purpose |
| --- | --- |
| `-f`, `--sqlite-file PATH` | Source SQLite database file. Required. |
| `-d`, `--mysql-database TEXT` | Target MySQL/MariaDB database name. Required. |
| `-u`, `--mysql-user TEXT` | MySQL/MariaDB user. Required. |
| `-p`, `--prompt-mysql-password` | Prompt for the MySQL password. Preferred for interactive use. |
| `--mysql-password TEXT` | Provide the MySQL password directly. Useful for automation, but handle carefully. |
| `-h`, `--mysql-host TEXT` | MySQL host. Defaults to `localhost`. |
| `-P`, `--mysql-port INTEGER` | MySQL port. Defaults to `3306`. |
| `-k`, `--mysql-socket PATH` | MySQL Unix socket path. Cannot be combined with SSL certificate options. |
| `-t`, `--sqlite-tables TUPLE` | Transfer only the listed tables. Implies no foreign key transfer. |
| `-e`, `--exclude-sqlite-tables TUPLE` | Transfer every table except the listed tables. Implies no foreign key transfer. |
| `-A`, `--sqlite-views-as-tables` | Materialize SQLite views as MySQL tables instead of creating MySQL views. |
| `-X`, `--without-foreign-keys` | Do not create foreign keys in MySQL. |
| `-W`, `--ignore-duplicate-keys` | Skip duplicate SQLite index names instead of renaming them with a numeric suffix. |
| `-E`, `--mysql-truncate-tables` | Truncate matching target tables before inserting data. |
| `-K`, `--mysql-skip-create-tables` | Skip table/view creation and transfer data only. |
| `-J`, `--mysql-skip-transfer-data` | Create schema only and skip table data. |
| `-i`, `--mysql-insert-method [DEFAULT\|IGNORE\|UPDATE]` | Choose duplicate-row insert behavior. Defaults to `IGNORE`. |
| `--mysql-integer-type TEXT` | MySQL default integer column type. Defaults to `INT(11)`. |
| `--mysql-string-type TEXT` | MySQL default string column type. Defaults to `VARCHAR(255)`. |
| `--mysql-text-type [LONGTEXT\|MEDIUMTEXT\|TEXT\|TINYTEXT]` | MySQL default text column type. Defaults to `TEXT`. |
| `--mysql-charset TEXT` | MySQL database and table character set. Defaults to `utf8mb4`. |
| `--mysql-collation TEXT` | MySQL database and table collation. Must belong to the selected charset. |
| `--mysql-ssl-ca PATH` | Path to an SSL CA certificate file. |
| `--mysql-ssl-cert PATH` | Path to an SSL client certificate file. Must be paired with `--mysql-ssl-key`. |
| `--mysql-ssl-key PATH` | Path to an SSL client key file. Must be paired with `--mysql-ssl-cert`. |
| `-S`, `--skip-ssl` | Disable MySQL connection encryption. Cannot be used with SSL certificate options. |
| `-T`, `--use-fulltext` | Use FULLTEXT indexes on text columns when the target server supports InnoDB FULLTEXT. |
| `--with-rowid` | Transfer SQLite `rowid` columns for tables that have rowids. |
| `-c`, `--chunk INTEGER` | Read and write SQL records in batches. |
| `-l`, `--log-file PATH` | Write logs to a file. |
| `-q`, `--quiet` | Show only errors after the initial command banner. |
| `--debug` | Re-raise exceptions for debugging instead of printing friendly errors. |
| `--version` | Show environment and dependency versions. |
| `--help` | Show CLI help. |

## Combinations and caveats

- `--sqlite-tables` and `--exclude-sqlite-tables` are mutually exclusive.
- Either table filter (`--sqlite-tables` or `--exclude-sqlite-tables`) automatically disables foreign key transfer.
- `--mysql-skip-create-tables` and `--mysql-skip-transfer-data` cannot be used together because there would be nothing to
  do.
- `--mysql-skip-create-tables` requires compatible target MySQL tables to already exist.
- `--mysql-truncate-tables` deletes rows from matching target tables before inserting data.
- `--mysql-socket` cannot be combined with `--mysql-ssl-ca`, `--mysql-ssl-cert`, or `--mysql-ssl-key`.
- `--skip-ssl` cannot be combined with `--mysql-ssl-ca`, `--mysql-ssl-cert`, or `--mysql-ssl-key`.
- `--mysql-ssl-cert` and `--mysql-ssl-key` must be provided together.
- `--mysql-collation` must be valid for the selected `--mysql-charset`.
- `--use-fulltext` fails before transfer starts when the target server does not support InnoDB FULLTEXT indexes.
- Native MySQL views are created by default. If a target table has the same name as a SQLite view, that target table is
  dropped before the MySQL view is created. Use `--sqlite-views-as-tables` for the older materialized-table behavior.
- Table, view, column, index, and constraint names are truncated to MySQL's 64-character identifier limit.
- `--mysql-password` passes the password as a command-line argument. Prefer `--prompt-mysql-password` for interactive use
  and inject secrets through a secret manager or CI secret store for automation.

MySQL SSL note: when `--mysql-ssl-ca` is provided, MySQL Connector/Python verifies the server certificate chain.
`--mysql-ssl-cert` and `--mysql-ssl-key` enable client certificate authentication. These options do not enable hostname
identity verification. If you provide only the client certificate and key without `--mysql-ssl-ca`, the server
certificate is not verified.

## MySQL, MariaDB, and SQLite notes

- MySQL and MariaDB are similar but not identical. JSON behavior, expression defaults, duplicate-key update SQL,
  timestamp defaults, fractional seconds, and FULLTEXT support can differ by server family and version.
- SQLite `JSONB` maps to MySQL/MariaDB `JSON` only when the target supports JSON: MySQL `>= 5.7.8` and MariaDB
  `>= 10.2.7`. Otherwise it maps to the configured text type.
- SQLite `JSONB` value conversion requires SQLite 3.45 or newer. With older SQLite versions, JSONB columns can still be
  selected, but the SQLite `json()` conversion function is not used during transfer.
- `--mysql-insert-method UPDATE` uses the MySQL `VALUES (...) AS __new__` alias only on MySQL `>= 8.0.19`; MariaDB keeps
  the older duplicate-key update form.
- Expression defaults are supported on MySQL `>= 8.0.13` and MariaDB `>= 10.2.0`; older servers may require defaults to
  be omitted or simplified.
- `CURRENT_TIMESTAMP` defaults on `DATETIME` require MySQL `>= 5.6.5` or MariaDB `>= 10.0.1`.
- Fractional seconds require MySQL `>= 5.6.4` or MariaDB `>= 10.1.2`.
- InnoDB FULLTEXT indexes require MySQL `>= 5.6.0` or MariaDB `>= 10.0.5`.
- After transfer, verify schema details that are important to your application, especially defaults, collations, JSONB
  columns, views, and foreign keys.

## Documentation

- [Full documentation](https://techouse.github.io/sqlite3-to-mysql/)
- [Changelog](CHANGELOG.md)
- [Issue tracker](https://github.com/techouse/sqlite3-to-mysql/issues)

## License

SQLite3 to MySQL is released under the [MIT License](LICENSE).
