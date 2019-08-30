"""Wrappers for exceptions that exist in Python 3 are missing in Python 2."""


class FileNotFoundError(IOError):  # pylint: disable=W0622
    """Substitute missing exception for Python 2."""

    pass  # pylint: disable=W0107


class ConnectionError(IOError):  # pylint: disable=W0622, W0107
    """Substitute missing exception for Python 2."""

    pass  # pylint: disable=W0107


class ConnectionAbortedError(IOError):  # pylint: disable=W0622, W0107
    """Substitute missing exception for Python 2."""

    pass  # pylint: disable=W0107
