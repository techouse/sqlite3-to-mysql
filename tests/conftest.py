from collections import namedtuple
from contextlib import contextmanager
from os.path import join
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
        "--mysql-version",
        dest="mysql_version",
        default="latest",
        help="Run the tests against a specific MySQL Docker image. Defaults to latest. "
        "Check all supported versions here https://hub.docker.com/_/mysql",
    )

    parser.addoption(
        "--mysql-port",
        dest="mysql_port",
        type=int,
        default=3307,
        help="Bind the MySQL from the Docker container to this port. Defaults to 3307. "
        "Change this in case you already have something running on port 3307!",
    )


def pytest_keyboard_interrupt():
    client = docker.from_env()
    for container in client.containers.list():
        if container.name == "pytest_sqlite3_to_mysql":
            container.kill()
            break


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
def fake_sqlite_database(faker, tmpdir_factory):
    temp_data_dir = tmpdir_factory.mktemp("data")
    temp_image_dir = tmpdir_factory.mktemp("images")
    db_file = join(str(temp_data_dir), "db.sqlite3")
    db = Database("sqlite:///{}".format(db_file))

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

    return db_file


@pytest.fixture(scope="session")
def mysql_credentials(pytestconfig):
    MySQLCredentials = namedtuple(
        "MySQLCredentials", ["user", "password", "host", "port", "database"]
    )
    return MySQLCredentials(
        user="tester",
        password="testpass",
        host="0.0.0.0",
        port=pytestconfig.getoption("mysql_port") or 3307,
        database="test_db",
    )


@pytest.fixture(scope="session")
def docker_mysql(mysql_credentials, pytestconfig):
    """ Connecting to a MySQL server within a Docker container is quite tricky :P
        Read more on the issue here https://hub.docker.com/_/mysql#no-connections-until-mysql-init-completes
    """
    try:
        client = docker.from_env()
    except Exception as err:
        pytest.fail(str(err))
        raise

    mysql_version = pytestconfig.getoption("mysql_version") or "latest"

    if not any("mysql:latest" in image.tags for image in client.images.list()):
        print("Attempting to download Docker image 'mysql:{}'".format(mysql_version))
        try:
            client.images.pull("mysql:{}".format(mysql_version))
        except (HTTPError, NotFound) as err:
            pytest.fail(str(err))
            raise

    container = client.containers.run(
        image="mysql:{}".format(mysql_version),
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

    mysql_connection = None
    mysql_available = False
    mysql_connection_retries = 15  # failsafe

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
                # sleep for a second and retry the connection
                sleep(1)
            else:
                raise
        finally:
            mysql_connection_retries -= 1
            if mysql_connection and mysql_connection.is_connected():
                mysql_available = True
                mysql_connection.close()
    else:
        if not mysql_available and mysql_connection_retries <= 0:
            container.kill()
            raise ConnectionAbortedError(
                "Maximum MySQL connection retries exhausted! Are you sure MySQL is running?"
            )

    yield container

    container.kill()


@pytest.fixture()
def fake_mysql_database(docker_mysql, mysql_credentials):
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
        cursor.execute("""DROP DATABASE IF EXISTS `{}`""".format(mysql_credentials.database))
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
