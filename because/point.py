from typing import (
    Any,
)

class Point(object):
    """Point representation for internal use.

    This makes format strings and argument passing slightly tidier.
    """
    def __init__(self, x, y):
        # type: (Any, Any) -> None
        self.x = x
        self.y = y
