SQLite3 to MySQL
================

A Python CLI for transferring SQLite 3 schema and data to MySQL or MariaDB.

|PyPI| |PyPI - Downloads| |Homebrew Formula Downloads| |PyPI - Python Version|
|MySQL Support| |MariaDB Support| |GitHub license| |Contributor Covenant|
|PyPI - Format| |Code style: black| |Codacy Badge| |Test Status| |CodeQL Status|
|Publish PyPI Package Status| |codecov| |GitHub Sponsors| |GitHub stars|

Installation
------------

.. code-block:: bash

   pip install sqlite3-to-mysql

Basic Usage
-----------

Use the password prompt for interactive use:

.. code-block:: bash

   sqlite3mysql -f ./app.sqlite3 -d app_db -u app_user -p -h 127.0.0.1 -P 3306

Tested Databases
----------------

See the `GitHub Actions CI matrix
<https://github.com/techouse/sqlite3-to-mysql/blob/master/.github/workflows/test.yml>`__
for the current MySQL and MariaDB versions tested by the project.

Common Tasks
------------

- Use ``--mysql-skip-transfer-data`` to create schema only.
- Use ``--mysql-skip-create-tables`` to transfer data into an existing MySQL schema.
- Use either table filter (``--sqlite-tables`` or
  ``--exclude-sqlite-tables``) to transfer a table subset; this disables
  foreign key transfer.
- Use ``--mysql-ssl-ca``, ``--mysql-ssl-cert``, and ``--mysql-ssl-key`` for
  certificate-based MySQL connections.

See :doc:`README` for full recipes, option notes, and MySQL/MariaDB caveats.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   README
   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. |PyPI| image:: https://img.shields.io/pypi/v/sqlite3-to-mysql?logo=pypi
   :target: https://pypi.org/project/sqlite3-to-mysql/
.. |PyPI - Downloads| image:: https://img.shields.io/pypi/dm/sqlite3-to-mysql?logo=pypi&label=PyPI%20downloads
   :target: https://pypistats.org/packages/sqlite3-to-mysql
.. |Homebrew Formula Downloads| image:: https://img.shields.io/homebrew/installs/dm/sqlite3-to-mysql?logo=homebrew&label=Homebrew%20downloads
   :target: https://formulae.brew.sh/formula/sqlite3-to-mysql
.. |PyPI - Python Version| image:: https://img.shields.io/pypi/pyversions/sqlite3-to-mysql?logo=python
   :target: https://pypi.org/project/sqlite3-to-mysql/
.. |MySQL Support| image:: https://img.shields.io/static/v1?logo=mysql&label=MySQL&message=5.5+%7C+5.6+%7C+5.7+%7C+8.0+%7C+8.4+%7C+9.7&color=2b5d80
   :target: https://github.com/techouse/sqlite3-to-mysql/actions/workflows/test.yml
.. |MariaDB Support| image:: https://img.shields.io/static/v1?logo=mariadb&label=MariaDB&message=5.5+%7C+10.0+%7C+10.6+%7C+10.11+%7C+11.4+%7C+11.8&color=C0765A
   :target: https://github.com/techouse/sqlite3-to-mysql/actions/workflows/test.yml
.. |GitHub license| image:: https://img.shields.io/github/license/techouse/sqlite3-to-mysql
   :target: https://github.com/techouse/sqlite3-to-mysql/blob/master/LICENSE
.. |Contributor Covenant| image:: https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg?logo=contributorcovenant
   :target: CODE-OF-CONDUCT.md
.. |PyPI - Format| image:: https://img.shields.io/pypi/format/sqlite3-to-mysql?logo=python
   :target: https://pypi.org/project/sqlite3-to-mysql/
.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg?logo=python
   :target: https://github.com/ambv/black
.. |Codacy Badge| image:: https://api.codacy.com/project/badge/Grade/d33b59d35b924711aae9418741a923ae
   :target: https://www.codacy.com/manual/techouse/sqlite3-to-mysql?utm_source=github.com&utm_medium=referral&utm_content=techouse/sqlite3-to-mysql&utm_campaign=Badge_Grade
.. |Test Status| image:: https://github.com/techouse/sqlite3-to-mysql/actions/workflows/test.yml/badge.svg
   :target: https://github.com/techouse/sqlite3-to-mysql/actions/workflows/test.yml
.. |CodeQL Status| image:: https://github.com/techouse/sqlite3-to-mysql/actions/workflows/github-code-scanning/codeql/badge.svg
   :target: https://github.com/techouse/sqlite3-to-mysql/actions/workflows/github-code-scanning/codeql
.. |Publish PyPI Package Status| image:: https://github.com/techouse/sqlite3-to-mysql/actions/workflows/publish.yml/badge.svg
   :target: https://github.com/techouse/sqlite3-to-mysql/actions/workflows/publish.yml
.. |codecov| image:: https://codecov.io/gh/techouse/sqlite3-to-mysql/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/techouse/sqlite3-to-mysql
.. |GitHub Sponsors| image:: https://img.shields.io/github/sponsors/techouse?logo=github
   :target: https://github.com/sponsors/techouse
.. |GitHub stars| image:: https://img.shields.io/github/stars/techouse/sqlite3-to-mysql.svg?style=social&label=Star&maxAge=2592000
   :target: https://github.com/techouse/sqlite3-to-mysql/stargazers
