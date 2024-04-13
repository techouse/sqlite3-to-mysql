"""Module containing bug report helper(s).

Adapted from https://github.com/psf/requests/blob/master/requests/help.py
"""

import platform
import sqlite3
import sys
import typing as t
from shutil import which
from subprocess import check_output

import click
import mysql.connector
import pytimeparse2
import simplejson
import tabulate
import tqdm

from . import __version__ as package_version


def _implementation() -> str:
    """Return a dict with the Python implementation and version.

    Provide both the name and the version of the Python implementation
    currently running. For example, on CPython 2.7.5 it will return
    {'name': 'CPython', 'version': '2.7.5'}.

    This function works best on CPython and PyPy: in particular, it probably
    doesn't work for Jython or IronPython. Future investigation should be done
    to work out the correct shape of the code for those platforms.
    """
    implementation: str = platform.python_implementation()

    if implementation == "CPython":
        implementation_version = platform.python_version()
    elif implementation == "PyPy":
        implementation_version = "%s.%s.%s" % (
            sys.pypy_version_info.major,  # type: ignore # noqa: ignore=E1101 pylint: disable=E1101
            sys.pypy_version_info.minor,  # type: ignore # noqa: ignore=E1101 pylint: disable=E1101
            sys.pypy_version_info.micro,  # type: ignore # noqa: ignore=E1101 pylint: disable=E1101
        )
        rel = sys.pypy_version_info.releaselevel  # type: ignore # noqa: ignore=E1101 pylint: disable=E1101
        if rel != "final":
            implementation_version = "".join([implementation_version, rel])
    elif implementation == "Jython":
        implementation_version = platform.python_version()  # Complete Guess
    elif implementation == "IronPython":
        implementation_version = platform.python_version()  # Complete Guess
    else:
        implementation_version = "Unknown"

    return f"{implementation} {implementation_version}"


def _mysql_version() -> str:
    if which("mysql") is not None:
        try:
            mysql_version: t.Union[str, bytes] = check_output(["mysql", "-V"])
            try:
                return mysql_version.decode().strip()  # type: ignore
            except (UnicodeDecodeError, AttributeError):
                return str(mysql_version)
        except Exception:  # nosec pylint: disable=W0703
            pass
    return "MySQL client not found on the system"


def info() -> t.List[t.List[str]]:
    """Generate information for a bug report."""
    try:
        platform_info = f"{platform.system()} {platform.release()}"
    except IOError:
        platform_info = "Unknown"

    return [
        ["sqlite3-to-mysql", package_version],
        ["", ""],
        ["Operating System", platform_info],
        ["Python", _implementation()],
        ["MySQL", _mysql_version()],
        ["SQLite", sqlite3.sqlite_version],
        ["", ""],
        ["click", click.__version__],
        ["mysql-connector-python", mysql.connector.__version__],
        ["pytimeparse2", pytimeparse2.__version__],
        ["simplejson", simplejson.__version__],  # type: ignore
        ["tabulate", tabulate.__version__],
        ["tqdm", tqdm.__version__],
    ]
