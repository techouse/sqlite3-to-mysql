# SQLite3 to MySQL

#### A simple Python 3 script to transfer the data from SQLite 3 to MySQL. 

I originally wrote this simple program as a standalone script and published it
as a [gist](https://gist.github.com/techouse/4deb94eee58a02d104c6) as an answer
to this [Stack Overflow question](https://stackoverflow.com/questions/18671/quick-easy-way-to-migrate-sqlite3-to-mysql/32243979#32243979).
Since then quite some people have taken interest in it since it's so simple and
effective. Therefore I finally moved my lazy bones and made a GitHub repository :octopus:.

### Usage
```
usage: sqlite3mysql.py [-h] [--sqlite-file SQLITE_FILE]
                       [--mysql-user MYSQL_USER]
                       [--mysql-password MYSQL_PASSWORD]
                       [--mysql-database MYSQL_DATABASE]
                       [--mysql-host MYSQL_HOST]
                       [--mysql-integer-type MYSQL_INTEGER_TYPE]
                       [--mysql-string-type MYSQL_STRING_TYPE]

optional arguments:
  -h, --help            show this help message and exit
  --sqlite-file SQLITE_FILE
                        SQLite3 db file
  --mysql-user MYSQL_USER
                        MySQL user
  --mysql-password MYSQL_PASSWORD
                        MySQL password
  --mysql-database MYSQL_DATABASE
                        MySQL host
  --mysql-host MYSQL_HOST
                        MySQL host
  --mysql-integer-type MYSQL_INTEGER_TYPE
                        MySQL default integer field type
  --mysql-string-type MYSQL_STRING_TYPE
                        MySQL default string field type
```
