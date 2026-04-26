---
name: sqlite3-to-mysql
description: Use this skill whenever a user wants to transfer, migrate, convert, troubleshoot, or generate commands for moving SQLite 3 schema and data into MySQL or MariaDB using sqlite3mysql. This skill helps gather the required source and connection details, choose a local or Docker workflow, produce safe copy-pasteable commands, and explain sqlite3mysql caveats.
---

# sqlite3mysql Transfer Assistant

Help users plan and run `sqlite3mysql` transfers from SQLite 3 into MySQL or MariaDB. Focus on user migration outcomes,
not on project development.

## Start With Inputs

Before giving a final command, collect any missing details that materially affect the command:

- Source SQLite file path for `-f` / `--sqlite-file`.
- Target database name for `-d` / `--mysql-database`.
- MySQL/MariaDB user for `-u` / `--mysql-user`.
- Host and port when the server is not local; default to `localhost` and `3306` only when that matches the user's setup.
- Whether the target should be reached over TCP, a Unix socket, or SSL/TLS.
- Runtime preference: installed CLI, PyPI install, Homebrew install, or Docker image.
- Whether they need a full transfer, schema only, data into an existing schema, selected tables, excluded tables,
  truncating before import, duplicate-row updates, FULLTEXT indexes, rowid transfer, views as tables, or custom
  MySQL types/charset/collation.
- Target server family and version when compatibility matters: MySQL and MariaDB differ for JSON, expression defaults,
  duplicate-key update SQL, timestamp defaults, fractional seconds, and FULLTEXT support.

Do not ask users to paste database passwords. Prefer `-p` / `--prompt-mysql-password` for interactive commands. Use
`--mysql-password` only for automation examples, and tell users to provide it through their secret-management mechanism
rather than hard-coding it. Warn that `--mysql-password` still places the secret in process argv where process listings,
logs, or shell history can expose it.

## Command Defaults

Use this full-transfer command as the base local pattern:

```bash
sqlite3mysql \
    --sqlite-file ./app.sqlite3 \
    --mysql-database app_db \
    --mysql-user app_user \
    --prompt-mysql-password \
    --mysql-host 127.0.0.1 \
    --mysql-port 3306
```

Use short flags when the user asks for a compact command:

```bash
sqlite3mysql -f ./app.sqlite3 -d app_db -u app_user -p -h 127.0.0.1 -P 3306
```

For Docker, mount the working directory and use `host.docker.internal` when MySQL or MariaDB runs on the host machine.
On Linux Docker Engine, include `--add-host=host.docker.internal:host-gateway` before the image name when the user is on
Linux or says `host.docker.internal` does not resolve:

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

If the CLI is not installed, give the installation command that matches the user's platform:

```bash
pip install sqlite3-to-mysql
```

```bash
brew install sqlite3-to-mysql
```

## Recipes

Use these options to adapt the base command:

- Schema only: add `--mysql-skip-transfer-data`.
- Data only into an existing MySQL schema: add `--mysql-skip-create-tables`; tell the user the target tables must already
  exist and be compatible.
- Selected tables: add `--sqlite-tables table_a table_b`; note that foreign keys are not transferred for table subsets.
- Excluded tables: add `--exclude-sqlite-tables audit_log temp_imports`; note that foreign keys are not transferred for
  table subsets.
- Refresh target rows: add `--mysql-truncate-tables`; warn that this deletes rows from matching target tables first.
- Duplicate rows: keep default `IGNORE`, add `--mysql-insert-method DEFAULT` to fail on duplicates, or add
  `--mysql-insert-method UPDATE` to update existing rows.
- Unix socket: add `--mysql-socket /path/to/mysqld.sock`; do not combine this with SSL certificate options.
- SSL CA verification: add `--mysql-ssl-ca /path/to/ca.pem`.
- Client certificate authentication: add `--mysql-ssl-cert /path/to/client-cert.pem --mysql-ssl-key /path/to/client-key.pem`,
  usually with `--mysql-ssl-ca`.
- Large transfers: tune `--chunk 50000` when needed.
- Views: by default, SQLite views become MySQL views; add `--sqlite-views-as-tables` only when the user wants
  materialized tables.
- FULLTEXT: add `--use-fulltext` only when the target server supports InnoDB FULLTEXT indexes.
- Rowids: add `--with-rowid` only when the user needs SQLite `rowid` values copied.

## Combinations To Check

Warn before producing commands with these invalid or risky combinations:

- `--sqlite-tables` and `--exclude-sqlite-tables` are mutually exclusive.
- Either table filter (`--sqlite-tables` or `--exclude-sqlite-tables`) disables foreign key transfer.
- `--mysql-skip-create-tables` and `--mysql-skip-transfer-data` cannot be used together because there would be nothing
  to do.
- `--mysql-skip-create-tables` alone requires existing compatible target MySQL tables.
- `--mysql-truncate-tables` deletes rows from matching target tables before inserting data.
- `--mysql-socket` cannot be combined with `--mysql-ssl-ca`, `--mysql-ssl-cert`, or `--mysql-ssl-key`.
- `--skip-ssl` cannot be combined with `--mysql-ssl-ca`, `--mysql-ssl-cert`, or `--mysql-ssl-key`.
- `--mysql-ssl-cert` and `--mysql-ssl-key` must be provided together.
- `--mysql-collation` must belong to the selected `--mysql-charset`.
- `--use-fulltext` fails early when the target server does not support InnoDB FULLTEXT indexes.
- Native MySQL views are created by default. If a target table has the same name as a SQLite view, that target table is
  dropped before the MySQL view is created.
- `--mysql-password` exposes the password through process argv and may leak through process listings, logs, or shell
  history; prefer `--prompt-mysql-password` for interactive use and never suggest literal passwords.

## MySQL, MariaDB, And SQLite Notes

Use these notes when users ask about compatibility or results:

- Use the GitHub Actions CI matrix as the source of truth for currently tested MySQL and MariaDB versions.
- MySQL and MariaDB have drifted; JSON behavior, expression defaults, duplicate-key update SQL, timestamp defaults,
  fractional seconds, and FULLTEXT support can differ by version.
- SQLite `JSONB` maps to MySQL/MariaDB `JSON` only when the target supports JSON: MySQL `>= 5.7.8` and MariaDB
  `>= 10.2.7`. Otherwise it maps to the configured text type.
- SQLite `JSONB` value conversion uses SQLite's `json()` function only on SQLite 3.45 or newer.
- `--mysql-insert-method UPDATE` uses the MySQL `VALUES (...) AS __new__` alias only on MySQL `>= 8.0.19`; MariaDB keeps
  the older duplicate-key update form.
- Expression defaults: MySQL `>= 8.0.13`, MariaDB `>= 10.2.0`.
- `CURRENT_TIMESTAMP` defaults on `DATETIME`: MySQL `>= 5.6.5`, MariaDB `>= 10.0.1`.
- Fractional seconds: MySQL `>= 5.6.4`, MariaDB `>= 10.1.2`.
- InnoDB FULLTEXT indexes: MySQL `>= 5.6.0`, MariaDB `>= 10.0.5`.
- MySQL identifier names are limited to 64 characters; long source names are truncated.
- Users should verify important defaults, collations, JSONB columns, views, and foreign keys after transfer.

## Response Shape

For command-generation requests, answer with:

1. A short statement of assumptions, especially source file, host, port, runtime, target database, and whether `-p` will
   prompt for the password.
2. One copy-pasteable command.
3. A brief caveats section only for options used in that command.
4. A verification suggestion such as checking the target with `SHOW TABLES;` or running application-specific checks.

Keep commands concrete. Use placeholders only when the user has not provided a required value, and label them clearly,
such as `./app.sqlite3`, `app_db`, `app_user`, or `/path/to/ca.pem`.
