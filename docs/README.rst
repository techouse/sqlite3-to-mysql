Usage
-----

Options
^^^^^^^

The command line options for the ``sqlite3mysql`` tool are as follows:

.. code-block:: bash

   sqlite3mysql [OPTIONS]

Required Options
""""""""""""""""

- ``-f, --sqlite-file PATH``: SQLite3 database file  [required]
- ``-d, --mysql-database TEXT``: MySQL database name  [required]
- ``-u, --mysql-user TEXT``: MySQL user  [required]

Password Options
""""""""""""""""

- ``-p, --prompt-mysql-password``: Prompt for MySQL password
- ``--mysql-password TEXT``: MySQL password

Connection Options
""""""""""""""""""

- ``-h, --mysql-host TEXT``: MySQL host. Defaults to localhost.
- ``-P, --mysql-port INTEGER``: MySQL port. Defaults to 3306.
- ``--mysql-socket PATH``: Path to MySQL unix socket file. Cannot be used together with ``--mysql-ssl-*`` options.
- ``--mysql-ssl-ca PATH``: Path to SSL CA certificate file. Cannot be used together with ``--mysql-socket``.
- ``--mysql-ssl-cert PATH``: Path to SSL certificate file. Must be provided together with ``--mysql-ssl-key``. Cannot be used together with ``--mysql-socket``.
- ``--mysql-ssl-key PATH``: Path to SSL key file. Must be provided together with ``--mysql-ssl-cert``. Cannot be used together with ``--mysql-socket``.
- ``-S, --skip-ssl``: Disable MySQL connection encryption. Cannot be used together with ``--mysql-ssl-*`` options.

MySQL SSL note: when ``--mysql-ssl-ca`` is provided, MySQL Connector/Python verifies the server
certificate chain. ``--mysql-ssl-cert`` and ``--mysql-ssl-key`` enable client certificate
authentication. These options do not enable hostname identity verification. If you provide only the
client certificate and key without ``--mysql-ssl-ca``, the server certificate is not verified.

Transfer Options
""""""""""""""""

- ``-t, --sqlite-tables TUPLE``: Transfer only these specific tables (space separated table names). Implies ``--without-foreign-keys`` which inhibits the transfer of foreign keys. Can not be used together with ``--exclude-sqlite-tables``.
- ``-e, --exclude-sqlite-tables TUPLE``: Exclude these specific tables (space separated table names). Implies ``--without-foreign-keys`` which inhibits the transfer of foreign keys. Can not be used together with ``--sqlite-tables``.
- ``-A, --sqlite-views-as-tables``: Materialize SQLite views as tables in MySQL instead of creating matching MySQL views (legacy behavior).
- ``-E, --mysql-truncate-tables``: Truncates existing tables before inserting data.
- ``-K, --mysql-skip-create-tables``: Skip creating tables in MySQL.
- ``-i, --mysql-insert-method [UPDATE|IGNORE|DEFAULT]``: MySQL insert method. DEFAULT will throw errors when encountering duplicate records; UPDATE will update existing rows; IGNORE will ignore insert errors. Defaults to IGNORE.
- ``-J, --mysql-skip-transfer-data``: Skip transferring data to MySQL.
- ``--mysql-integer-type TEXT``: MySQL default integer field type. Defaults to INT(11).
- ``--mysql-string-type TEXT``: MySQL default string field type. Defaults to VARCHAR(255).
- ``--mysql-text-type [LONGTEXT|MEDIUMTEXT|TEXT|TINYTEXT]``: MySQL default text field type. Defaults to TEXT.
- ``--mysql-charset TEXT``: MySQL database and table character set. Defaults to utf8mb4.
- ``--mysql-collation TEXT``: MySQL database and table collation.
- ``-T, --use-fulltext``: Use FULLTEXT indexes on TEXT columns. Will throw an error if your MySQL version does not support InnoDB FULLTEXT indexes!
- ``-X, --without-foreign-keys``: Do not transfer foreign keys.
- ``-W, --ignore-duplicate-keys``: Ignore duplicate keys. The default behavior is to create new ones with a numerical suffix, e.g. 'existing_key' -> 'existing_key_1'
- ``--with-rowid``: Transfer rowid columns.
- ``-c, --chunk INTEGER``: Chunk reading/writing SQL records

Other Options
"""""""""""""

- ``-l, --log-file PATH``: Log file
- ``-q, --quiet``: Quiet. Display only errors.
- ``--debug``: Debug mode. Will throw exceptions.
- ``--version``: Show the version and exit.
- ``--help``: Show help message and exit.

Docker
^^^^^^

If you don’t want to install the tool on your system, you can use the
Docker image instead.

.. code:: bash

   docker run -it \
       --workdir $(pwd) \
       --volume $(pwd):$(pwd) \
       --rm ghcr.io/techouse/sqlite3-to-mysql:latest \
       --sqlite-file baz.db \
       --mysql-user foo \
       --mysql-password bar \
       --mysql-database baz \
       --mysql-host host.docker.internal

This will mount your host current working directory (pwd) inside the
Docker container as the current working directory. Any files Docker
would write to the current working directory are written to the host
directory where you did docker run. Note that you have to also use a
`special
hostname <https://docs.docker.com/desktop/networking/#use-cases-and-workarounds-for-all-platforms>`__
``host.docker.internal`` to access your host machine from inside the
Docker container.

Homebrew
^^^^^^^^

If you’re on macOS, you can install the tool using
`Homebrew <https://brew.sh/>`__.

.. code:: bash

   brew install sqlite3-to-mysql
   sqlite3mysql --help
