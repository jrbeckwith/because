"""Common and base exception classes for the package.
"""
from typing import (
    Any,
    Optional,
    Text,
)


class BecauseError(Exception):
    """Base class for exceptions raised from inside the package.
    """


class ParseError(BecauseError):
    """An error happened while parsing a response body.

    E.g. a JSONDecodeError
    """
    def __init__(
            self,
            message,        # type: Text
            response=None,  # type: Optional[Any]
            error=None,     # type: Optional[Exception]
    ):
        # type: (...) -> None

        self.message = message
        self.response = response
        self.error = error

        super(ParseError, self).__init__(message)


class InvalidObject(BecauseError):
    """Base class for errors where a valid object could not be created.

    This is meant to be raised from __init__ to prevent instances with bizarre
    states from ever being exposed for use. When used in this way, the
    expression invoking the constructor does not return an object to bind a
    name to. So the silly instance does not cause downstream exceptions far
    from the cause of the problem. Also, code consuming instances can safely
    assume that the instances are not completely bizarre.
    """
    def __init__(self, message):
        # type: (Text) -> None
        super(InvalidObject, self).__init__(message)
