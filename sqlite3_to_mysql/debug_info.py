"""Module containing bug report helper(s).

Adapted from https://github.com/psf/requests/blob/master/requests/help.py
"""

from __future__ import print_function

import platform
import sqlite3
import sys
from subprocess import check_output

import click
import mysql.connector
import pytimeparse
import simplejson as json
import six
import tqdm

from . import __version__ as package_version


def _implementation():
    """Return a dict with the Python implementation and version.

    Provide both the name and the version of the Python implementation
    currently running. For example, on CPython 2.7.5 it will return
    {'name': 'CPython', 'version': '2.7.5'}.

    This function works best on CPython and PyPy: in particular, it probably
    doesn't work for Jython or IronPython. Future investigation should be done
    to work out the correct shape of the code for those platforms.
    """
    implementation = platform.python_implementation()

    if implementation == "CPython":
        implementation_version = platform.python_version()
    elif implementation == "PyPy":
        implementation_version = "%s.%s.%s" % (
            sys.pypy_version_info.major,  # noqa: ignore=E1101 pylint: disable=E1101
            sys.pypy_version_info.minor,  # noqa: ignore=E1101 pylint: disable=E1101
            sys.pypy_version_info.micro,  # noqa: ignore=E1101 pylint: disable=E1101
        )
        rel = (
            sys.pypy_version_info.releaselevel  # noqa: ignore=E1101 pylint: disable=E1101
        )
        if rel != "final":
            implementation_version = "".join([implementation_version, rel])
    elif implementation == "Jython":
        implementation_version = platform.python_version()  # Complete Guess
    elif implementation == "IronPython":
        implementation_version = platform.python_version()  # Complete Guess
    else:
        implementation_version = "Unknown"

    return {"name": implementation, "version": implementation_version}


def _mysql_version():
    try:
        mysql_version = check_output(["mysql", "-V"])
        try:
            return mysql_version.decode().strip()
        except (UnicodeDecodeError, AttributeError):
            return mysql_version
    except FileNotFoundError:
        return "MySQL not found on the system"


def info():
    """Generate information for a bug report."""
    try:
        platform_info = {
            "system": platform.system(),
            "release": platform.release(),
        }
    except IOError:
        platform_info = {
            "system": "Unknown",
            "release": "Unknown",
        }

    return {
        "platform": platform_info,
        "implementation": _implementation(),
        "mysql": {"version": _mysql_version()},
        "sqlite": {"version": sqlite3.sqlite_version},
        "mysql-connector-python": {"version": mysql.connector.__version__},
        "click": {"version": click.__version__},
        "six": {"version": six.__version__},
        "tqdm": {"version": tqdm.__version__},
        "pytimeparse": {"version": pytimeparse.__version__},
        "simplejson": {"version": json.__version__},
        "sqlite3-to-mysql": {"version": package_version.__version__},
    }


def main():
    """Pretty-print the bug information as JSON."""
    print(json.dumps(info(), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
