"""Storage for HTTP request and response headers.

This storage does not "know" anything about HTTP, it just preserves all the
information that may be needed per HTTP standards.
"""
from typing import (
    Any,
    DefaultDict,
    List,
    Optional,
    Sequence,
    Iterator,
    Text,
    Tuple,
)
import collections
from . reprs import ReprMixin
from . pretty import PrettyMixin
from . utils import is_iterable
from . errors import InvalidObject


class InvalidHeaders(InvalidObject):
    """Raised instead of making a headers object with invalid state.

    The distinction of this from InvalidHeader is that this is generally raised
    when creating a Headers instance, but since InvalidHeader is an instance of
    InvalidHeaders the distinction is not so important.
    """


class InvalidHeader(InvalidHeaders):
    """Raised instead of modifying a header in an invalid way.

    This implies that the current operation, if allowed to continue, would make
    a headers object with invalid state.

    This exception subclasses InvalidHeaders so that you can catch problems
    with just one header, or catch all problems relating to headers.
    """


class Headers(ReprMixin, PrettyMixin):
    """Storage for HTTP headers.

    This is basically a mutable collection of (name, value) bytestrings,
    but it must also satisfy a few special considerations that make it
    unsatisfying to use a list of tuples.

    For efficiency, values must be indexed by header name. Otherwise a list
    would have to be traversed, e.g., to find the values of a particular
    header, to delete a particular header, to ensure a header is not
    duplicated, etc.
    
    Header names are case-insensitive, so keys have to be internally
    normalized.

    When there are multiple headers of the same name, all the values must be
    stored instead of just one. So if you just use a dict, you are eventually
    going to find cases where that doesn't work.

    Header ordering does not generally matter -- *except* for ordering among
    headers with the same name, which must be preserved. So one can't use sets.

    Both of those considerations are handled by storing a list for each header
    name.

    This list is exposed to allow operations like insert, append and remove
    without writing a lot of new methods on this class.

    Lastly, it's not a big deal, but when the same complex kind of list or dict
    gets passed around a lot, there tend to be a lot of exposed interfaces
    which each have the same largish set of ways to choke on degenerate
    structures. If the standard interchange format for headers in your code is
    List[Tuple[Text, List[Text]]] there are a lot of things that some code
    somewhere could get wrong, so you might as well formalize the arrangement.
    """

    def __init__(self, pairs=None):
        # type: (Optional[Sequence[Tuple[Text, Text]]]) -> None
        """
        :arg pairs:
            A sequence of (header_name, header_value) tuples, where both
            header_name and header_value must be bytes.
        """
        # Set up internal state
        self._data = collections.defaultdict(list)  # type: DefaultDict[Text, list]

        if not pairs:
            return

        # Python normally frowns on explicit type checks, but we literally need
        # bytes to send over the wire here, or callers will pass stuff that
        # needs to be serialized and/or encoded in ways we could only guess.
        # The try/except noise is to ensure users get good feedback on errors
        try:
            iter(pairs)
        except TypeError:
            raise InvalidHeaders(
                "cannot initialize with value of type {0!r}"
                .format(type(pairs))
            )
        for pair in pairs:
            try:
                key, value = pair
            except (TypeError, ValueError):
                raise InvalidHeader(
                    "cannot unpack as pair: {0!r}".format(pair)
                )
            if not isinstance(key, bytes):
                raise InvalidHeader("key is not bytes: {0!r}".format(key))
            if not isinstance(value, bytes):
                raise InvalidHeader("key is not bytes: {0!r}".format(key))
            self[key].append(value)

    def copy(self):
        # type: () -> Headers
        """Create a new instance with the same contents.

        The main use for this is to make defensive copies of a Headers instance
        that you want to pass to another unit without allowing that unit to
        make changes. Otherwise, there is normally no reason to use this.
        """
        return type(self)(pairs=list(self.pairs()))

    def __eq__(self, other):
        # type: (Any) -> bool
        """Compare the contents of two instances, as in h1 == h2.
        """
        return bool(self._data == other._data)

    # TODO: ensure defensive copy on all input

    def __getitem__(self, key):
        # type: (Text) -> List[Text]
        """Fetch all values under the given key.

        Always returns a list; if header is not set, this list is empty.
        """
        # No defensive copy - return the actual list.
        # This means user can append, insert, etc. without having to
        # reimplement that stuff.
        return self._data[key.lower()]

    def __setitem__(self, key, values):
        # type: (Text, List[Text]) -> None
        """Write all values under the given key.

        The provided values replace all values previously set.
        """
        if not isinstance(key, bytes):
            raise InvalidHeader("key must be bytes")
        stringish = (type(u""), type(b""))
        if isinstance(values, stringish):
            raise InvalidHeader("values cannot have a string type")
        if not is_iterable(values):
            raise InvalidHeader("values must be iterable")
        # Defensive copy/any sequence, order matters, allow duplicate values
        self._data[key.lower()] = list(values)

    def __contains__(self, key):
        # type: (Text) -> bool
        return key.lower() in self._data

    def set(self, key, value):
        # type: (Text, Text) ->  None
        """Set one value for the given name.

        The provided value replaces all values previously set.

        This shortcut simply avoids the need to check for other values and
        supply a new list.
        """
        if isinstance(value, list):
            raise InvalidHeader("value can't be a list")
        key = key.lower()
        self._data[key][:] = []
        try:
            del self._data[key]
        except KeyError:
            pass
        assert key not in self._data
        assert self._data[key] == []
        assert not isinstance(value, list)
        values = [value]
        assert values == [value]
        # assert value == 2, value

        self._data[key] = values

        # assert self._data[key] == [value]
        # self[key] = [value]

    @classmethod
    def merged(cls, *objs):
        # type: (*Headers) -> Headers
        """Make a copy with overrides from another object.

        Where there are no key collisions, the result has keys from all the
        passed objects. Otherwise, objects earlier in the list are overridden
        from objects later in the list.
        """
        instance = cls()
        for obj in objs:
            # Allow e.g. {} to signify an empty headers list
            if not obj:
                continue
            for key, values in obj.items():
                instance[key] = values

        return instance

    def unset(self, key):
        # type: (Text) -> None
        """Remove all values for the given name.

        If the name isn't set, this does nothing.

        This is just a shortcut for a common need.
        """
        del self._data[key.lower()]

    def add(self, key, value):
        # type: (Text, Text) -> None
        """Append the given value under the given key.

        h.add(k, v) is just a nicer spelling for h[k].append(v).
        """
        self._data[key.lower()].append(value)

    def keys(self):
        # type: () -> Iterator[Text]
        """Give the keys set in this instance, as dict.keys().
        """
        return (
            key.capitalize() for key in self._data.keys()
        )

    def values(self):
        # type: () -> List[List[Text]]
        """Give the values lists set in this instance, as dict.values().

        Note the subtle distinction here that this gives a list of lists,
        with one list for each key, rather than a flat list of values.
        """
        return list(self._data.values())

    def items(self):
        # type: () -> Iterator[Tuple[Text, List[Text]]]
        """Return (key, values) pairs, as in dict.items.

        Note the subtle distinction of this from pairs(). items() returns
        (key, values) tuples: Tuple[Text, List[Text]]. pairs() returns
        (key, value) tuples: Tuple[Text, Text].

        The capitalization of the keys is normalized on the way out.
        """
        return (
            (key.capitalize(), value)
            for key, value in self._data.items()
        )

    def pairs(self):
        # type: () -> Iterator[Tuple[Text, Text]]
        """Get all of the items in this instance as pairs.

        Note the subtle distinction of this from items(). items() returns (key,
        values) tuples: Tuple[Text, List[Text]]. pairs() returns (key, value)
        tuples: Tuple[Text, Text].

        Returns an iterator of (header_name, header_value) pairs.
        """
        for key, values in self.items():
            for value in values:
                yield (key, value)

    def combined_pairs(self):
        """Get all the items as pairs with multivalues joined by commas.

        This sort of combination is as per RFC 2616 4.2 and may be needed by
        implementations like httplib which only accept a single value per key.
        """
        for key, values in self.items():
            yield key, b",".join(values)

    def repr_data(self):
        return collections.OrderedDict([
            ("pairs", list(self.pairs()))
        ])

    @classmethod
    def coerce(cls, obj):
        # type: (Any) -> Headers
        """Turn the given object into an instance, if it's obvious how to.

        Putting this into a separate classmethod/constructor allows the
        constructor not to be crazily polymorphic but also allows all kinds of
        conceivably sensible conversions in a way that is explicitly marked.
        """
        data = []  # type: Sequence[Tuple[Text, Text]]

        # For ordered types, preserve the existing ordering
        if isinstance(obj, cls):
            data = list(obj.pairs())
        if isinstance(obj, collections.OrderedDict):
            data = list(obj.items())
        elif isinstance(obj, collections.Sequence):
            data = obj

        # Otherwise, sort on ingestion for determinism
        elif isinstance(obj, collections.Mapping):
            data = sorted(obj.items())
        elif isinstance(obj, collections.Set):
            data = sorted(obj)

        # If all else fails, just complain
        else:
            raise InvalidHeaders("cannot coerce from {0!r}".format(type(obj)))

        return cls(data)

    def pretty_tuples(self):
        # type: () -> List[Tuple[Text, Any]]
        return list(self.pairs())
