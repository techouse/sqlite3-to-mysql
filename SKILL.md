---
name: sqlite3-to-mysql
description: Generate safe sqlite3mysql commands and migration guidance for transferring SQLite 3 databases to MySQL or MariaDB. Use this skill whenever the user wants to move, copy, migrate, import, sync, or test data from SQLite into MySQL or MariaDB, especially when they mention sqlite3-to-mysql, sqlite3mysql, table filters, SSL, sockets, existing tables, foreign keys, views, JSONB, or MySQL/MariaDB compatibility.
---

# SQLite3 To MySQL Command Helper

Use this skill to help users plan and run `sqlite3mysql` transfers. Prefer producing a concrete command plus a short
explanation of important caveats. Do not invent unsupported options.

## Gather Inputs

Before finalizing a command, determine:

- SQLite source path: `--sqlite-file`.
- Target connection: `--mysql-database`, `--mysql-user`, and one of host/port or socket.
- Password handling: prefer `--prompt-mysql-password` for interactive use. Use `--mysql-password` only for
  non-interactive automation when the value is injected by a CI secret store or secret manager, and warn that it still
  places the secret in process argv where process listings, logs, or shell history can expose it.
- Transfer scope: all tables, `--sqlite-tables`, or `--exclude-sqlite-tables`.
- Existing-table behavior: create missing tables, `--mysql-skip-create-tables`, `--mysql-skip-transfer-data`, or
  `--mysql-truncate-tables`.
- Duplicate-row behavior: default `IGNORE`, explicit `DEFAULT`, or `UPDATE`.
- Schema details: custom integer/string/text types, charset/collation, rowid transfer, FULLTEXT indexes, views as tables.
- Transport security: default TLS behavior, `--skip-ssl`, CA verification, client certificate authentication, or Unix
  socket.
- Target server family and version when compatibility matters: MySQL and MariaDB differ for JSON, expression defaults,
  FULLTEXT, and duplicate-key update SQL.

If a required value is unknown, show placeholders rather than guessing.

## Command Patterns

Basic interactive transfer:

```bash
sqlite3mysql \
    --sqlite-file path/to/app.sqlite3 \
    --mysql-database app_db \
    --mysql-user app_user \
    --prompt-mysql-password
```

Non-interactive automation with a secret-managed environment variable:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user --mysql-password "$MYSQL_PASSWORD"
```

When using this pattern, tell the user to inject `MYSQL_PASSWORD` from a CI secret store or secret manager and avoid
logging expanded commands.

Non-default TCP host and port:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p -h 127.0.0.1 -P 3307
```

Selected tables:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p --sqlite-tables users posts comments
```

Exclude tables:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p --exclude-sqlite-tables audit_logs cache_entries
```

Schema only:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p --mysql-skip-transfer-data
```

Data into existing tables:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p --mysql-skip-create-tables
```

Truncate first:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p --mysql-truncate-tables
```

Update rows on duplicate keys:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p --mysql-insert-method UPDATE
```

Unix socket:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p --mysql-socket /var/run/mysqld/mysqld.sock
```

TLS with CA verification:

```bash
sqlite3mysql -f app.sqlite3 -d app_db -u app_user -p --mysql-ssl-ca /path/to/ca.pem
```

TLS with client certificate authentication:

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

Docker:

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

When suggesting Docker, explain that `--mysql-password` is still a CLI argument inside the container. Prefer
`--prompt-mysql-password` for interactive runs; for automation, inject `MYSQL_PASSWORD` from a secret manager or CI
secret store and avoid logging expanded commands.

## Invalid or Risky Combinations

Never suggest these combinations:

- `--sqlite-tables` with `--exclude-sqlite-tables`.
- `--mysql-skip-create-tables` with `--mysql-skip-transfer-data`.
- `--mysql-socket` with any `--mysql-ssl-*` option.
- `--skip-ssl` with any `--mysql-ssl-*` option.
- `--mysql-ssl-cert` without `--mysql-ssl-key`, or `--mysql-ssl-key` without `--mysql-ssl-cert`.
- `--mysql-collation` values that do not belong to the selected `--mysql-charset`.

Warn about these cases:

- `--sqlite-tables` and `--exclude-sqlite-tables` imply `--without-foreign-keys`.
- `--mysql-skip-create-tables` assumes compatible target tables already exist.
- `--mysql-truncate-tables` deletes existing rows from matching target tables before inserting.
- Native view creation drops any target table with the same name as a SQLite view before creating the MySQL view.
- `--mysql-password` exposes the password through process argv and may leak through process listings, logs, or shell
  history; prefer `--prompt-mysql-password` for interactive use and never suggest literal passwords.
- `--mysql-insert-method DEFAULT` lets duplicate records fail.
- `--use-fulltext` fails early when the target server does not support InnoDB FULLTEXT indexes.
- `--mysql-ssl-cert` and `--mysql-ssl-key` without `--mysql-ssl-ca` authenticate the client but do not verify the server
  certificate.

## Compatibility Notes

- JSON support: MySQL `>= 5.7.8`, MariaDB `>= 10.2.7`; otherwise SQLite `JSONB` maps to the configured text type.
- SQLite `JSONB` value conversion uses SQLite's `json()` function only on SQLite 3.45 or newer.
- `UPDATE` insert mode uses MySQL's newer `VALUES (...) AS __new__` alias only on MySQL `>= 8.0.19`; MariaDB keeps the
  older duplicate-key update form.
- Expression defaults: MySQL `>= 8.0.13`, MariaDB `>= 10.2.0`.
- `CURRENT_TIMESTAMP` for `DATETIME`: MySQL `>= 5.6.5`, MariaDB `>= 10.0.1`.
- Fractional seconds: MySQL `>= 5.6.4`, MariaDB `>= 10.1.2`.
- InnoDB FULLTEXT indexes: MySQL `>= 5.6.0`, MariaDB `>= 10.0.5`.
- Identifiers are truncated to MySQL's 64-character limit.
- Native MySQL views are created by default; a target table with the same name as a SQLite view is dropped before the
  view is created. `--sqlite-views-as-tables` materializes SQLite views as MySQL tables instead.

## Response Shape

When answering a migration request:

1. Give the recommended command first.
2. State assumptions in one short paragraph or bullet list.
3. Call out any invalid combinations or destructive behavior.
4. Suggest `sqlite3mysql --help` for the complete local option reference.
