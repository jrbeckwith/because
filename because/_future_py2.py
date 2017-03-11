"""Python 2.7 implementation of Result.

This module is for internal use only. Do not use it directly. Import from
result to get the desired conditional import.

This module may only include syntax which parses in Python 2. If something
works on both Python 2 and 3, it belongs in the base class future._Result.
Otherwise, if it only should be present under Python 3, it should be in
_result_py3.py.
"""
import sys
from . _future_base import _Result, _Present
assert sys.version_info[:2] == (2, 7), "this module requires Python 2.7"


class Result(_Result):
    # Use the same docstring across all implementations.
    __doc__ = _Result._doc

    # Here we can't use e.g. "yield from".


class Present(_Present):
    __doc__ = _Present._doc
