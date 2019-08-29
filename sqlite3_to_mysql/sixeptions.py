""" This module contains wrappers for exceptions that exist in Python 3 but are not present in Python 2
"""


class FileNotFoundError(IOError):
    pass


class ConnectionError(IOError):
    pass


class ConnectionAbortedError(IOError):
    pass
