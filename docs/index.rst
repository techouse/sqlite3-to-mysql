SQLite3 to MySQL
================

A simple Python tool to transfer data from SQLite 3 to MySQL

|PyPI| |PyPI - Downloads| |PyPI - Python Version| |MySQL Support| |MariaDB Support|
|GitHub license| |Contributor Covenant| |PyPI - Format| |Code style: black|
|Codacy Badge| |Test Status| |CodeQL Status| |Publish PyPI Package Status|
|Publish Docker Image| |codecov| |GitHub Sponsors| |GitHub stars|

Installation
------------

.. code:: bash

   pip install sqlite3-to-mysql

Basic Usage
-----------

.. code:: bash

   sqlite3mysql -f path/to/foo.sqlite -d foo_db -u foo_user -p

.. toctree::
   :maxdepth: 4
   :caption: Contents:

   README
   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. |PyPI| image:: https://img.shields.io/pypi/v/sqlite3-to-mysql
   :target: https://pypi.org/project/sqlite3-to-mysql/
.. |PyPI - Downloads| image:: https://img.shields.io/pypi/dm/sqlite3-to-mysql
   :target: https://pypistats.org/packages/sqlite3-to-mysql
.. |PyPI - Python Version| image:: https://img.shields.io/pypi/pyversions/sqlite3-to-mysql
   :target: https://pypi.org/project/sqlite3-to-mysql/
.. |MySQL Support| image:: https://img.shields.io/static/v1?label=MySQL&message=5.5+%7C+5.6+%7C+5.7+%7C+8.0&color=2b5d80
   :target: https://img.shields.io/static/v1?label=MySQL&message=5.6+%7C+5.7+%7C+8.0&color=2b5d80
.. |MariaDB Support| image:: https://img.shields.io/static/v1?label=MariaDB&message=5.5+%7C+10.0+%7C+10.1+%7C+10.2+%7C+10.3+%7C+10.4+%7C+10.5+%7C+10.6%7C+10.11&color=C0765A
   :target: https://img.shields.io/static/v1?label=MariaDB&message=10.0+%7C+10.1+%7C+10.2+%7C+10.3+%7C+10.4+%7C+10.5&color=C0765A
.. |GitHub license| image:: https://img.shields.io/github/license/techouse/sqlite3-to-mysql
   :target: https://github.com/techouse/sqlite3-to-mysql/blob/master/LICENSE
.. |Contributor Covenant| image:: https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg
   :target: CODE-OF-CONDUCT.md
.. |PyPI - Format| image:: https://img.shields.io/pypi/format/sqlite3-to-mysql
   :target: (https://pypi.org/project/sqlite3-to-mysql/)
.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/ambv/black
.. |Codacy Badge| image:: https://api.codacy.com/project/badge/Grade/d33b59d35b924711aae9418741a923ae
   :target: https://www.codacy.com/manual/techouse/sqlite3-to-mysql?utm_source=github.com&utm_medium=referral&utm_content=techouse/sqlite3-to-mysql&utm_campaign=Badge_Grade
.. |Test Status| image:: https://github.com/techouse/sqlite3-to-mysql/actions/workflows/test.yml/badge.svg
   :target: https://github.com/techouse/sqlite3-to-mysql/actions/workflows/test.yml
.. |CodeQL Status| image:: https://github.com/techouse/sqlite3-to-mysql/actions/workflows/codeql-analysis.yml/badge.svg
   :target: https://github.com/techouse/sqlite3-to-mysql/actions/workflows/codeql-analysis.yml
.. |Publish PyPI Package Status| image:: https://github.com/techouse/sqlite3-to-mysql/actions/workflows/publish.yml/badge.svg
   :target: https://github.com/techouse/sqlite3-to-mysql/actions/workflows/publish.yml
.. |Publish Docker Image| image:: https://github.com/techouse/sqlite3-to-mysql/actions/workflows/docker.yml/badge.svg
   :target: https://github.com/techouse/sqlite3-to-mysql/actions/workflows/docker.yml
.. |codecov| image:: https://codecov.io/gh/techouse/sqlite3-to-mysql/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/techouse/sqlite3-to-mysql
.. |GitHub Sponsors| image:: https://img.shields.io/github/sponsors/techouse
   :target: https://github.com/sponsors/techouse
.. |GitHub stars| image:: https://img.shields.io/github/stars/techouse/sqlite3-to-mysql.svg?style=social&label=Star&maxAge=2592000
   :target: https://github.com/techouse/sqlite3-to-mysql/stargazers