import pytest
import collections
from because.headers import (
    Headers,
    InvalidHeader,
    InvalidHeaders,
)


class TestHeaders(object):

    def test_init_empty(self):
        """Test behavior of an empty instance.
        """
        headers = Headers()
        assert list(headers.keys()) == []
        assert list(headers.values()) == []
        assert list(headers.items()) == []
        assert list(headers.pairs()) == []

    def test_init_simple(self):
        """Test behavior of a simple instance.
        """
        values = [(b"K1", b"v1"), (b"K2", b"v2")]
        headers = Headers(values)
        assert sorted(headers.keys()) == [b"K1", b"K2"]
        assert sorted(headers.values()) == [[b"v1"], [b"v2"]]
        assert sorted(headers.items()) == [
            (b"K1", [b"v1"]),
            (b"K2", [b"v2"]),
        ]
        assert sorted(headers.pairs()) == values

    @pytest.mark.parametrize("value", [
        3.14,
        u"Herp",
        b"Derp",
        [b"foo", b"bar"],
    ])
    def test_init_foolish(self, value):
        """Test the result of passing foolish things to the constructor.

        This means things that couldn't possibly work.
        """
        with pytest.raises(InvalidHeaders):
            Headers(value)

    @pytest.mark.parametrize("value", [
        {b"foo": b"bar"},
    ])
    def test_init_questionable(self, value):
        """Test the result of passing questionable things to the constructor.

        This means things that people might suppose to work, except we're
        intentionally shunting all of the polymorphism into coerce().
        """
        with pytest.raises(InvalidHeaders):
            Headers(value)

    def test_init_nonbytes_key(self):
        """Verify that headers rejects keys and values that are not bytes.

        Otherwise problems may tend to occur down the line, when the culprit is
        no longer on the call stack.
        """
        with pytest.raises(InvalidHeader):
            Headers([(u"foo", b"bar")])

    def test_init_nonbytes_value(self):
        with pytest.raises(InvalidHeader):
            Headers([(b"foo", u"bar")])

    @pytest.mark.parametrize("key", [
        None,
        [b"foo"],
    ])
    def test_setitem_key_foolish(self, key):
        headers = Headers()
        with pytest.raises(InvalidHeader):
            headers[key] = [b"bar"]

    @pytest.mark.parametrize("value", [
        None,
        3.14,
        b"foo",
    ])
    def test_setitem_value_foolish(self, value):
        headers = Headers()
        with pytest.raises(InvalidHeader):
            headers[b"foo"] = value

    def test_setitem_getitem(self):
        headers = Headers()

        # Initial set
        headers[b"foo"] = [b"bar"]
        assert headers[b"foo"] == [b"bar"]

        # Overwrite
        headers[b"foo"] = [b"baz"]
        assert headers[b"foo"] == [b"baz"]

    def test_setitem_multiple(self):
        headers = Headers()
        headers[b"foo"] = [b"bar", b"baz"]
        assert headers[b"foo"] == [b"bar", b"baz"]

    def test_set_simple(self):
        headers = Headers()
        headers.set(b"X1", b"y1")
        assert list(headers.pairs()) == [(b"X1", b"y1")]

    def test_set_overwrite(self):
        headers = Headers()
        headers.set(b"X", b"y1")
        assert list(headers.pairs()) == [(b"X", b"y1")]
        # Overwrite
        headers.set(b"X", b"y2")
        assert list(headers.pairs()) == [(b"X", b"y2")]

    def test_unset_simple(self):
        headers = Headers()
        headers[b"Foo"] = [b"bar"]
        assert headers[b"Foo"] == [b"bar"]
        headers.unset(b"Foo")
        assert headers[b"Foo"] == []

    def test_add_simple(self):
        headers = Headers()
        headers.add(b"X1", b"y1")
        headers.add(b"X2", b"y2")
        assert sorted(headers.pairs()) == [(b"X1", b"y1"), (b"X2", b"y2")]

    def test_add_duplicate(self):
        headers = Headers()
        headers.add(b"X", b"y1")
        headers.add(b"X", b"y2")
        assert list(headers.pairs()) == [(b"X", b"y1"), (b"X", b"y2")]

    def test_repr(self):
        headers = Headers()
        headers.add(b"X", b"y")
        text = repr(headers)
        assert text == "Headers(pairs=[(b'X', b'y')])"

    def test_eq(self):
        # The repetition here is deliberate
        values1 = [(b"X", b"y")]
        values2 = [(b"X", b"y")]
        # They are supposed to have distinct identities for this test
        assert values1 is not values2
        # But they are still supposed to be equal
        assert values1 == values2
        # And the same for the headers instances
        headers1 = Headers(values1)
        headers2 = Headers(values2)
        assert headers1 == headers2

    @pytest.mark.parametrize("given", [
        [(b"1", b"2"), (b"X", b"y")],
        collections.OrderedDict([(b"1", b"2"), (b"X", b"y")]),
        {b"X": b"y", b"1": b"2"},
        set([(b"X", b"y"), (b"1", b"2")]),
    ])
    def test_coerce_reasonable(self, given):
        expected = [(b"1", b"2"), (b"X", b"y")]
        headers = Headers.coerce(given)
        assert sorted(headers.pairs()) == expected

