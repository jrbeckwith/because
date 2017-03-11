import collections
try:
    import reprlib
except ImportError:
    import repr as reprlib  # type: ignore
from typing import (
    Any,
)

_REPR_LOOKS_GOOD = u"b" in repr(b"")


class _Repr(reprlib.Repr):

    def repr_str(self, obj, _):
        # type: (Any, Any) -> str
        if _REPR_LOOKS_GOOD:
            result = repr(obj)
        else:
            result = "b" + repr(obj)
        return result


THE_REPR = _Repr()


def consistent_repr(obj):
    # type: (Any) -> str
    """repr() which uses the b"" prefix on Python2
    """
    return THE_REPR.repr(obj)



class ReprMixin(object):
    """Mixin for creating nice __repr__ methods.

    1. Define a repr_data() method to return a dict of the attributes you
       want in the repr. If you care about ordering, have this return an
       OrderedDict.

    2. Inherit this class to get a __repr__ method.

    The provided __repr__ has the following useful properties:

    * It shows important attributes instead of a memory address
    * It always orders attributes consistently
    * It shows the names of attributes instead of just listing values
    * It consistently uses the b"" prefix across Python versions
    * It resembles a constructor call
    """

    def repr_data(self):
        """Override this to specify what data to show in __repr__ returns.
        """
        return collections.OrderedDict([])

    def __repr__(self):
        # type: () -> str
        """Debug representation for tracebacks, logs, shell, etc.
        """
        cls_name = type(self).__name__
        attributes = self.repr_data()
        if not isinstance(attributes, collections.OrderedDict):
            keys = sorted(attributes.keys())
        else:
            keys = list(attributes.keys())
        reprs = [
            "{0}={1}".format(key, consistent_repr(attributes[key]))
            for key in keys
        ]
        signature = ", ".join(reprs)
        return "{0}({1})".format(cls_name, signature)


__all__ = ["consistent_repr", "ReprMixin"]
