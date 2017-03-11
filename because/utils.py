from typing import (
    Any,
)

def is_iterable(obj):
    # type: (Any) -> bool
    """Shortcut to test if an object is iterable.
    """
    try:
        iter(obj)
    except TypeError:
        return False
    return True
