import pytest
from because.response import (
    Response,
    InvalidResponse,
)
from because.headers import (
    InvalidHeaders,
)


class TestResponse(object):

    @pytest.mark.parametrize("value", [
        None,
        3.14,
        [],
    ])
    def test_init_status_unexpected(self, value):
        with pytest.raises(InvalidResponse):
            Response(status=value)

    @pytest.mark.parametrize("value", [
        3.14,
        u"String",
    ])
    def test_init_headers_unexpected(self, value):
        with pytest.raises(InvalidHeaders):
            Response(400, headers=value)

    @pytest.mark.parametrize("value", [
        u"this is text, not bytes",
        (b"what", b"a tuple?"),
        {b"maybe": b"json?"},
    ])
    def test_init_body_unexpected(self, value):
        with pytest.raises(InvalidResponse):
            Response(b"GET", b"/foo", body=value)

    def test_equal_true(self):
        requests = [
            Response(400),
            Response(400),
        ]
        assert requests[1] == requests[0]

    def test_equal_false(self):
        requests = [
            Response(400),
            Response(500),
        ]
        assert requests[1] != requests[0]

    def test_repr(self):
        request = Response(400, headers=[
            (b"Wonky", b"urgh"),
        ])
        text = repr(request)
        assert text == (
            "Response(status=400, "
            "headers=[(b'Wonky', b'urgh')], "
            "body=b'')"
        )

    def test_repr_round_trip(self):
        request = Response(400, body=b"fnar")
        text = repr(request)
        print("eval'ing {0!r}".format(text))
        clone = eval(text)
        assert clone == request

