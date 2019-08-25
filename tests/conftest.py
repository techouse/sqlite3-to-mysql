import socket
from collections import namedtuple
from contextlib import contextmanager
from os.path import join, isfile, realpath
from time import sleep

import docker
import mysql.connector
import pytest
from docker.errors import NotFound
from mysql.connector import errorcode
from requests import HTTPError
from sqlalchemy.exc import IntegrityError

from .database import Database
from .factories import AuthorFactory, TagFactory, ArticleFactory, ImageFactory


def pytest_addoption(parser):
    parser.addoption(
        "--sqlite-file",
        dest="sqlite_file",
        default=None,
        help="SQLite database file. Defaults to none and generates one internally.",
    )

    parser.addoption(
        "--mysql-user",
        dest="mysql_user",
        default="tester",
        help="MySQL user. Defaults to 'tester'.",
    )

    parser.addoption(
        "--mysql-password",
        dest="mysql_password",
        default="testpass",
        help="MySQL password. Defaults to 'testpass'.",
    )

    parser.addoption(
        "--mysql-database",
        dest="mysql_database",
        default="test_db",
        help="MySQL database name. Defaults to 'test_db'.",
    )

    parser.addoption(
        "--mysql-host",
        dest="mysql_host",
        default="0.0.0.0",
        help="Test against a MySQL server running on this host. Defaults to '0.0.0.0'.",
    )

    parser.addoption(
        "--mysql-port",
        dest="mysql_port",
        type=int,
        default=None,
        help="The TCP port of the MySQL server.",
    )

    parser.addoption(
        "--no-docker",
        dest="use_docker",
        default=True,
        action="store_false",
        help="Do not use a Docker MySQL image to run the tests. "
        "If you decide to use this switch you will have to use a physical MySQL server.",
    )

    parser.addoption(
        "--docker-mysql-image",
        dest="docker_mysql_image",
        default="mysql:latest",
        help="Run the tests against a specific MySQL Docker image. Defaults to mysql:latest. "
        "Check all supported versions here https://hub.docker.com/_/mysql",
    )


@pytest.fixture(scope="session", autouse=True)
def cleanup_hanged_docker_containers():
    try:
        client = docker.from_env()
        for container in client.containers.list():
            if container.name == "pytest_sqlite3_to_mysql":
                container.kill()
                break
    except Exception:
        pass


def pytest_keyboard_interrupt():
    try:
        client = docker.from_env()
        for container in client.containers.list():
            if container.name == "pytest_sqlite3_to_mysql":
                container.kill()
                break
    except Exception:
        pass


class Helpers:
    @staticmethod
    @contextmanager
    def not_raises(exception):
        try:
            yield
        except exception:
            raise pytest.fail("DID RAISE {0}".format(exception))

    @staticmethod
    @contextmanager
    def session_scope(db):
        """Provide a transactional scope around a series of operations."""
        session = db.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


@pytest.fixture
def helpers():
    return Helpers


@pytest.fixture(scope="session")
def sqlite_database(pytestconfig, faker, tmpdir_factory):
    db_file = pytestconfig.getoption("sqlite_file")
    if db_file:
        if not isfile(realpath(db_file)):
            pytest.fail("{} does not exist".format(db_file))
            raise FileNotFoundError("{} does not exist".format(db_file))
        return realpath(db_file)

    temp_data_dir = tmpdir_factory.mktemp("data")
    temp_image_dir = tmpdir_factory.mktemp("images")
    db_file = temp_data_dir.join("db.sqlite3")
    db = Database("sqlite:///{}".format(str(db_file)))

    with Helpers.session_scope(db) as session:
        for _ in range(faker.pyint(min_value=12, max_value=24)):
            article = ArticleFactory()
            article.authors.append(AuthorFactory())
            article.tags.append(TagFactory())
            for _ in range(faker.pyint(min_value=1, max_value=4)):
                article.images.append(
                    ImageFactory(
                        path=join(
                            str(temp_image_dir),
                            faker.year(),
                            faker.month(),
                            faker.day_of_month(),
                            faker.file_name(extension="jpg"),
                        )
                    )
                )
            session.add(article)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()

    return str(db_file)


def is_port_in_use(port, host="0.0.0.0"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


@pytest.fixture(scope="session")
def mysql_credentials(pytestconfig):
    MySQLCredentials = namedtuple(
        "MySQLCredentials", ["user", "password", "host", "port", "database"]
    )

    port = pytestconfig.getoption("mysql_port") or 3306
    if pytestconfig.getoption("use_docker"):
        while is_port_in_use(port, pytestconfig.getoption("mysql_host")):
            if port >= 2 ** 16 - 1:
                pytest.fail(
                    "No ports appear to be available on the host {}".format(
                        pytestconfig.getoption("mysql_host")
                    )
                )
                raise ConnectionError(
                    "No ports appear to be available on the host {}".format(
                        pytestconfig.getoption("mysql_host")
                    )
                )
            port += 1

    return MySQLCredentials(
        user=pytestconfig.getoption("mysql_user") or "tester",
        password=pytestconfig.getoption("mysql_password") or "testpass",
        database=pytestconfig.getoption("mysql_database") or "test_db",
        host=pytestconfig.getoption("mysql_host") or "0.0.0.0",
        port=port,
    )


@pytest.fixture(scope="session", autouse=True)
def mysql_instance(mysql_credentials, pytestconfig):
    use_docker = pytestconfig.getoption("use_docker")
    container = None
    mysql_connection = None
    mysql_available = False
    mysql_connection_retries = 15  # failsafe

    if use_docker:
        """ Connecting to a MySQL server within a Docker container is quite tricky :P
            Read more on the issue here https://hub.docker.com/_/mysql#no-connections-until-mysql-init-completes
        """
        try:
            client = docker.from_env()
        except Exception as err:
            pytest.fail(str(err))
            raise

        docker_mysql_image = (
            pytestconfig.getoption("docker_mysql_image") or "mysql:latest"
        )

        if not any(docker_mysql_image in image.tags for image in client.images.list()):
            print("Attempting to download Docker image {}'".format(docker_mysql_image))
            try:
                client.images.pull(docker_mysql_image)
            except (HTTPError, NotFound) as err:
                pytest.fail(str(err))
                raise

        container = client.containers.run(
            image=docker_mysql_image,
            name="pytest_sqlite3_to_mysql",
            ports={
                "3306/tcp": (
                    mysql_credentials.host,
                    "{}/tcp".format(mysql_credentials.port),
                )
            },
            environment={
                "MYSQL_RANDOM_ROOT_PASSWORD": "yes",
                "MYSQL_USER": mysql_credentials.user,
                "MYSQL_PASSWORD": mysql_credentials.password,
                "MYSQL_DATABASE": mysql_credentials.database,
            },
            command=[
                "--character-set-server=utf8mb4",
                "--collation-server=utf8mb4_unicode_ci",
            ],
            detach=True,
            auto_remove=True,
        )

    while not mysql_available and mysql_connection_retries > 0:
        try:
            mysql_connection = mysql.connector.connect(
                user=mysql_credentials.user,
                password=mysql_credentials.password,
                host=mysql_credentials.host,
                port=mysql_credentials.port,
            )
        except mysql.connector.Error as err:
            if err.errno == errorcode.CR_SERVER_LOST:
                # sleep for two seconds and retry the connection
                sleep(2)
            else:
                raise
        finally:
            mysql_connection_retries -= 1
            if mysql_connection and mysql_connection.is_connected():
                mysql_available = True
                mysql_connection.close()
    else:
        if not mysql_available and mysql_connection_retries <= 0:
            raise ConnectionAbortedError(
                "Maximum MySQL connection retries exhausted! Are you sure MySQL is running?"
            )

    yield

    if use_docker:
        container.kill()


@pytest.fixture()
def mysql_database(mysql_instance, mysql_credentials):
    yield

    mysql_connection = mysql.connector.connect(
        user=mysql_credentials.user,
        password=mysql_credentials.password,
        host=mysql_credentials.host,
        port=mysql_credentials.port,
    )
    if not mysql_connection.is_connected():
        raise ConnectionError("Unable to connect to MySQL")

    cursor = mysql_connection.cursor()

    try:
        cursor.execute(
            """DROP DATABASE IF EXISTS `{}`""".format(mysql_credentials.database)
        )
        mysql_connection.commit()
    except mysql.connector.Error as err:
        pytest.fail(
            "Failed to drop MySQL database {}: {}".format(
                mysql_credentials.database, err
            )
        )
        raise
    finally:
        if mysql_connection.is_connected():
            cursor.close()
            mysql_connection.close()
