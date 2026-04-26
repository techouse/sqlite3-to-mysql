# Repository Guidelines

## Project Structure & Module Organization

- Application code lives in `src/sqlite3_to_mysql`; `cli.py` exposes the `sqlite3mysql` entry point, while
  `transporter.py`, `sqlite_utils.py`, and `mysql_utils.py` contain the transfer core.
- Tests sit in `tests/unit` for isolated modules and `tests/func` for CLI/integration coverage. Shared fixtures and
  factories are under `tests/factories.py` and `tests/database.py`.
- Generated artefacts belong in `build/`, `dist/`, `docs/_build/`, and `htmlcov/`; avoid committing edits to these
  directories and prefer changes in `src/`, `tests/`, or source docs.
- User-facing CLI behavior should stay aligned across `README.md`, `docs/README.rst`, and the agent-facing `SKILL.md`.

## Build, Test, and Development Commands

- Bootstrap a local env:
  `python3 -m venv env && source env/bin/activate && pip install -e . && pip install -r requirements_dev.txt`.
- Run targeted checks with `pytest -v --cov=src/sqlite3_to_mysql` to exercise both unit and functional suites.
- Execute the full automation set via `tox`; use `tox -e python3.14` for a single interpreter or `tox -e linters` for
  formatting, linting, typing, and security checks. `tox -e black` and `tox -e isort` will auto-format when needed.

## Coding Style & Naming Conventions

- Stick to Python 3.9–3.14 compatibility with explicit type hints (the package ships `py.typed`; tox also covers
  free-threaded Python 3.14t).
- Formatting is enforced by Black (120-character lines, 4-space indents) and isort with the Black profile; Flake8 (
  88-character soft cap) guards stylistic issues, so keep imports sorted and unused code pruned.
- Follow snake_case for modules/functions, UpperCamelCase for classes, and SCREAMING_SNAKE_CASE for constants. Prefer
  descriptive Click option names to match existing CLI patterns.

## Testing Guidelines

- Write `pytest` unit tests alongside the feature under `tests/unit/` and integration cases under `tests/func/`.
- Name tests `test_<module>_<behavior>` and colocate fixtures beside their usage; slower transfer scenarios belong in
  `tests/func`.
- A reachable MySQL instance is required for functional tests; a disposable container such as
  `docker run --rm -d -e MYSQL_ROOT_PASSWORD=test -p 3306:3306 mysql:8` satisfies dependencies with credentials from
  `tests/db_credentials.json`.
- New features should extend unit coverage and add regression tests whenever the SQLite ↔ MySQL mapping changes. Aim to
  keep `pytest --cov` green before submitting.

## Commit & Pull Request Guidelines

- Reuse the git history’s gitmoji prefix style (`:sparkles: add bulk row copy support`) and keep each commit scoped to a
  single concern.
- Reference related issues in commit bodies or the PR description, and update `CHANGELOG.md`, docs, and `SKILL.md` when
  user-facing behavior shifts.
- Before opening a PR, ensure `tox` completes successfully, document operational changes, and attach CLI logs or
  screenshots when UX output is affected.
