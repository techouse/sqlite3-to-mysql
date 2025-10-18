# AI Coding Agent Instructions for `sqlite3-to-mysql`

> Purpose: Help agents quickly contribute features or fixes to this SQLite → MySQL transfer tool while respecting project workflows and constraints.

## Architecture Snapshot
- Core package lives in `src/sqlite3_to_mysql/`.
  - `cli.py` defines the `sqlite3mysql` Click CLI and validates option interplay (mutual exclusions, implied flags).
  - `transporter.py` implements the end-to-end transfer in class `SQLite3toMySQL.transfer()`: create DB (if missing), create tables, optionally truncate, bulk insert (chunked or streamed), then indices and foreign keys.
  - `mysql_utils.py` & `sqlite_utils.py` encapsulate dialect/version feature checks, type adaptation and identifier safety (`safe_identifier_length`). Keep new MySQL capability gates here.
  - `types.py` provides typed param/attribute structures consumed via `Unpack` in `SQLite3toMySQL.__init__`.
- Data flow: CLI → construct `SQLite3toMySQL` → introspect SQLite schema via PRAGMA → create MySQL schema → transfer rows (streamed / chunked) → add indices → add foreign keys.
- Generated/ephemeral outputs: logs (optional), progress bars (`tqdm`), created MySQL objects.

## Key Behaviors & Patterns
- Table creation logic retries without DEFAULTs if MySQL rejects expression defaults (`_create_table` with `skip_default=True`). Preserve this two-pass approach when modifying default handling.
- MySQL feature detection stored as booleans (`_mysql_fulltext_support`, `_allow_expr_defaults`, etc.) set early in `__init__`. New conditional behaviors should follow this pattern.
- Column type translation centralised in `_translate_type_from_sqlite_to_mysql`; prefer extending mappings there rather than scattering conversions.
- DEFAULT value normalization handled by `_translate_default_for_mysql`; supports CURRENT_* and boolean coercion. Extend cautiously—return empty string to suppress invalid defaults.
- Identifier shortening: always wrap dynamic table/index/column names with `safe_identifier_length(...)` before emitting SQL.
- Index creation may recurse on duplicate names, appending numeric suffix. Respect `_ignore_duplicate_keys` to skip retries.
- Chunked data transfer controlled by `--chunk`; when present uses `fetchmany` loop, else full `fetchall` with `tqdm` progress.
- Foreign keys only added when neither table include/exclude filters nor `--without-foreign-keys` effective.

## CLI Option Conventions
- Mutually exclusive: `--sqlite-tables` vs `--exclude-sqlite-tables`; setting either implies `--without-foreign-keys`.
- Disallow simultaneous `-K` (skip create) and `-J` (skip transfer) — early exit.
- Insert method: `IGNORE` (default), `UPDATE` (uses ON DUPLICATE KEY UPDATE with optional VALUES alias), `DEFAULT` (no modifiers).

## Development Workflow
- Local env: `python3 -m venv env && source env/bin/activate && pip install -e . && pip install -r requirements_dev.txt`.
- Run tests with coverage: `pytest -v --cov=src/sqlite3_to_mysql` (unit: `tests/unit`, functional/CLI: `tests/func`). Functional tests need running MySQL (e.g. `docker run --rm -d -e MYSQL_ROOT_PASSWORD=test -p 3306:3306 mysql:8`). Credentials from `tests/db_credentials.json`.
- Full quality gate: `tox -e linters` (runs black, isort, flake8, pylint, bandit, mypy). Use `tox -e python3.12` for test subset.
- Formatting: Black (120 cols) + isort profile=black; Flake8 enforces 88-col soft cap—avoid long chained expressions in one line.

## Adding Features Safely
- Add new MySQL/SQLite capability checks in `mysql_utils.py` / `sqlite_utils.py`, expose booleans during `__init__` for downstream logic.
- For new CLI flags: define in `cli.py` above `cli()` with clear help text; maintain mutual exclusion patterns and keep error messages consistent with existing ones.
- Ensure new behavior gets unit tests (isolate pure functions) plus at least one functional test hitting the CLI.
- Avoid editing files in `build/`, `docs/_build`, `htmlcov/`—treat them as generated.

## Performance Considerations
- Prefer prepared cursors (`cursor(prepared=True)`) like existing code; batch inserts via `executemany`.
- Large transfers: encourage using `--chunk` to reduce memory footprint; any new bulk path must preserve commit granularity.

## Logging & Debugging
- Use `_logger` from class; don't print directly. Respect `quiet` flag for progress/INFO output; errors still emitted.
- Debug mode (`--debug`) surfaces exceptions instead of swallowing.

## Contribution Style
- Single-concern commits with gitmoji prefix (e.g., `:sparkles:` for features). Update `CHANGELOG.md` for user-facing changes.
- Preserve type hints; new public interfaces should be annotated and, if user-facing, reflected in docs (`docs/`).

---
Feedback welcome: Clarify any missing workflow, edge case, or pattern you need—request updates and this doc will iterate.
