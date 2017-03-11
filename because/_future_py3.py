"""Python 3.5+ implementation of Result.

This module is for internal use only. Do not use it directly. Import from
result to get the desired conditional import.

This module may include syntax which does not parse in Python 2. If something
works on both Python 2 and 3, it belongs in the base class future._Result.
Otherwise, if it only should be present under Python 2, it should be in
_result_py2.py.
"""
import sys
from . _future_base import _Result, _Present
assert sys.version_info >= (3, 5), "this module requires Python 3.5+"


class Result(_Result):
    # Use the same docstring across all implementations.
    __doc__ = _Result._doc

    # Since the import of this module is conditional on the version, we can use
    # "yield from" without fear that importing this module will create an
    # uncatchable SyntaxError.
    def __await__(self):
        # Just pass through whatever thingy the future gives us
        # This should work with any scheduler that uses await syntax
        response = yield from self._future.__await__()
        self._running_callback = True
        return self._callback(response)


class Present(_Present):
    __doc__ = _Present._doc

    def __await__(self):
        yield self._value
