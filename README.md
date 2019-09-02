[![PyPI](https://img.shields.io/pypi/v/sqlite3-to-mysql)](https://pypi.org/project/sqlite3-to-mysql/)
[![Downloads](https://pepy.tech/badge/sqlite3-to-mysql)](https://pepy.tech/project/sqlite3-to-mysql)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sqlite3-to-mysql)](https://pypi.org/project/sqlite3-to-mysql/)
[![GitHub license](https://img.shields.io/github/license/techouse/sqlite3-to-mysql)](https://github.com/techouse/sqlite3-to-mysql/blob/master/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Build Status](https://travis-ci.org/techouse/sqlite3-to-mysql.svg?branch=master)](https://travis-ci.org/techouse/sqlite3-to-mysql)
[![codecov](https://codecov.io/gh/techouse/sqlite3-to-mysql/branch/master/graph/badge.svg)](https://codecov.io/gh/techouse/sqlite3-to-mysql)

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

Options:
  -f, --sqlite-file PATH     SQLite3 db file  [required]
  -d, --mysql-database TEXT  MySQL database name  [required]
  -u, --mysql-user TEXT      MySQL user  [required]
  -p, --mysql-password TEXT  MySQL password
  -h, --mysql-host TEXT      MySQL host. Defaults to localhost.
  -P, --mysql-port INTEGER   MySQL port. Defaults to 3306.
  --mysql-integer-type TEXT  MySQL default integer field type. Defaults to
                             INT(11).
  --mysql-string-type TEXT   MySQL default string field type. Defaults to
                             VARCHAR(255).
  -c, --chunk INTEGER        Chunk reading/writing SQL records
  -l, --log-file PATH        Log file
  --help                     Show this message and exit.
```

### Testing
In order to run the test suite run these commands using a Docker MySQL image.

**Requires a running Docker instance!**

- using Python 2.7
```bash
git clone https://github.com/techouse/sqlite3-to-mysql
cd sqlite3-to-mysql
virtualenv -p $(which python2) env
source env/bin/activate
pip install -e .
pip install -r requirements_dev.txt
tox
```

- using Python 3.5+
```bash
git clone https://github.com/techouse/sqlite3-to-mysql
cd sqlite3-to-mysql                   
python3 -m venv env
source env/bin/activate
pip install -e .
pip install -r requirements_dev.txt
tox
```

### Note
After a __LONG__ time I finally found the time to write the complimentary script to transfer
[MySQL to SQLite3](https://github.com/techouse/mysql-to-sqlite3). Check it out :)


#### Additional note
Python **3.8** is currently **not** supported because at the moment of writing the most recent 
version of [MySQL Connector/Python](https://pypi.org/project/mysql-connector-python/) **v8.0.17** 
still contains a reference to a [feature deprecated in Python 3.5 and removed in Python 3.8](https://bugs.python.org/issue1322):
```
mysql/connector/connection.py:126: DeprecationWarning: dist() and linux_distribution() functions are deprecated in Python 3.5
```
[Check the failing build for yourself](https://travis-ci.org/techouse/sqlite3-to-mysql/jobs/579039451).