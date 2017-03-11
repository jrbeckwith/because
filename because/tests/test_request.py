import pytest
from because.request import (
    Request,
    InvalidRequest,
)


class TestRequest(object):

    @pytest.mark.parametrize("value", [
        u"GET",
    ])
    def test_init_method_unexpected(self, value):
        with pytest.raises(InvalidRequest):
            Request(value, b"/foo", body=b"whee")

    @pytest.mark.parametrize("value", [
        u"GET",
    ])
    def test_init_url_unexpected(self, value):
        with pytest.raises(InvalidRequest):
            Request(b"GET", value, body=b"whee")

    @pytest.mark.parametrize("value", [
        u"this is text, not bytes",
        (b"what", b"a tuple?"),
        {b"maybe": b"json?"},
    ])
    def test_init_body_unexpected(self, value):
        with pytest.raises(InvalidRequest):
            Request(b"GET", b"/foo", body=value)

    def test_equal_true(self):
        requests = [
            Request(b"GET", b"/foo"),
            Request(b"GET", b"/foo"),
        ]
        assert requests[1] == requests[0]

    def test_equal_false(self):
        requests = [
            Request(b"GET", b"/foo"),
            Request(b"GET", b"/bar"),
        ]
        assert requests[1] != requests[0]

    def test_repr(self):
        request = Request(b"GET", b"http://example.com/foo", headers=[
            (b"Accept", b"*"),
        ])
        text = repr(request)
        assert text == (
            "Request(method=b'GET', "
            "url=b'http://example.com/foo', "
            "headers=[(b'Accept', b'*')], body=None)"
        )

    def test_repr_round_trip(self):
        request = Request(b"GET", b"/foo", body=b"fnar")
        text = repr(request)
        print("eval'ing {0!r}".format(text))
        clone = eval(text)
        assert clone == request

