"""Wrappers for exceptions that exist in Python 3 are missing in Python 2."""


class FileNotFoundError(IOError):
    """Substitute missing exception for Python 2."""

    pass


class ConnectionError(IOError):
    """Substitute missing exception for Python 2."""

    pass


class ConnectionAbortedError(IOError):
    """Substitute missing exception for Python 2."""

    pass
