[![Build Status](https://travis-ci.org/techouse/sqlite3-to-mysql.svg?branch=master)](https://travis-ci.org/techouse/sqlite3-to-mysql)
[![codecov](https://codecov.io/gh/techouse/sqlite3-to-mysql/branch/master/graph/badge.svg)](https://codecov.io/gh/techouse/sqlite3-to-mysql)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# SQLite3 to MySQL

#### A simple Python 3 script to transfer the data from SQLite 3 to MySQL. 

I originally wrote this simple program as a standalone script and published it
as a [gist](https://gist.github.com/techouse/4deb94eee58a02d104c6) as an answer
to this [Stack Overflow question](https://stackoverflow.com/questions/18671/quick-easy-way-to-migrate-sqlite3-to-mysql/32243979#32243979).
Since then quite some people have taken interest in it since it's so simple and
effective. Therefore I finally moved my lazy bones and made a GitHub repository :octopus:.

### Installation
```bash
git clone https://github.com/techouse/sqlite3-to-mysql
cd sqlite3-to-mysql
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
python sqlite3mysql.py -h
```

### Usage
```
usage: sqlite3mysql.py [-h] -f SQLITE_FILE -u MYSQL_USER [-p MYSQL_PASSWORD]
                       -d MYSQL_DATABASE [-H MYSQL_HOST] [-P MYSQL_PORT]
                       [--mysql-integer-type MYSQL_INTEGER_TYPE]
                       [--mysql-string-type MYSQL_STRING_TYPE] [-c CHUNK]
                       [-l LOG_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -f SQLITE_FILE, --sqlite-file SQLITE_FILE
                        SQLite3 db file
  -u MYSQL_USER, --mysql-user MYSQL_USER
                        MySQL user
  -p MYSQL_PASSWORD, --mysql-password MYSQL_PASSWORD
                        MySQL password
  -d MYSQL_DATABASE, --mysql-database MYSQL_DATABASE
                        MySQL database name
  -H MYSQL_HOST, --mysql-host MYSQL_HOST
                        MySQL host
  -P MYSQL_PORT, --mysql-port MYSQL_PORT
                        MySQL port
  --mysql-integer-type MYSQL_INTEGER_TYPE
                        MySQL default integer field type
  --mysql-string-type MYSQL_STRING_TYPE
                        MySQL default string field type
  -c CHUNK, --chunk CHUNK
                        Chunk reading/writing SQL records
  -l LOG_FILE, --log-file LOG_FILE
                        Log file
```

### Testing
In order to run the test suite run these commands using a Docker MySQL image.

**Requires a running Docker instance!**
```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements-test.txt
pytest --cov=src
```

### Note
After a __LONG__ time I finally found the time to write the complimentary script to transfer
[MySQL to SQLite3](https://github.com/techouse/mysql-to-sqlite3). Check it out :)
