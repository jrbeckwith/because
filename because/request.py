from typing import (
    Any,
    Optional,
    Tuple,
    List,
    Text,
)
import collections
from . errors import InvalidObject
from . headers import Headers
from . reprs import ReprMixin
from . pretty import PrettyMixin


class InvalidRequest(InvalidObject):
    """Raised instead of creating an invalid Request instance.
    """


class Request(ReprMixin, PrettyMixin):
    """Represent parameters for making an HTTP request.

    You may be saying to yourself: "why yet another class Request?!?" Well --
    this internal representation is used to abstract over representations like
    QNetworkRequest, so that `because` can work about the same in multiple
    environments without all the response processing code having to be
    duplicated with minor variations in it.

    Excludes some important operational parameters, like SSL configuration and
    timeout duration, that do not really specify the request payload. This also
    does not represent a request as it is being performed. That's a Transfer.
    """
    def __init__(self, method, url, body=None, headers=None):
        # type: (bytes, bytes, Optional[bytes], Headers) -> None
        """
        :arg method:
            bytestring indicating the HTTP method to use.
        :arg url:
            bytestring containing the URL to request.
        :arg body:
            bytestring containing the request body.
        :arg headers:
            List of (name, value) tuples - both name and value being
            bytestrings - representing HTTP request headers to use. This
            representation is used because HTTP headers can be duplicated and
            some clients may care about their ordering.
        """
        self.method = self._init_method(method)     # type: bytes
        self.url = self._init_url(url)              # type: bytes
        self.body = self._init_body(body)           # type: Optional[bytes]
        self.headers = self._init_headers(headers)  # type: Headers
        # TODO: body streaming? painful to reuse body through a pipeline though

    def _init_method(self, value):
        # type: (Any) -> bytes
        if not isinstance(value, bytes):
            raise InvalidRequest("method must be bytes")
        return value

    def _init_url(self, value):
        # type: (Any) -> bytes
        if not isinstance(value, bytes):
            raise InvalidRequest("url must be bytes")
        return value

    def _init_body(self, value):
        # type: (Any) -> Optional[bytes]
        if value is not None and not isinstance(value, bytes):
            raise InvalidRequest("body must be bytes")
        return value

    def _init_headers(self, value):
        # type: (Any) -> Headers
        """Produce an internal representation of headers as a Headers object.
        """
        # Pass through Headers instances
        if isinstance(value, Headers):
            headers = value
        # Construct Headers instance from sequence of (name, value) pairs.
        elif value is not None:
            headers = Headers(value)
        # None or empty should get a new Headers instance
        elif not value:
            headers = Headers()
        return headers

    def __eq__(self, other):
        # type: (Any) -> bool
        """Compare two instances for equality.
        """
        attrs = ["method", "url", "body", "headers"]
        return all(
            getattr(self, attr) == getattr(other, attr)
            for attr in attrs
        )

    def repr_data(self):
        return collections.OrderedDict([
            ("method", self.method),
            ("url", self.url),
            ("headers", list(self.headers.pairs())),
            ("body", self.body),
        ])

    def pretty_tuples(self):
        # type: () -> List[Tuple[Text, Any]]
        """Get a debug representation of attributes as a list of tuples.

        This is really just used to customize the pretty_text() method provided
        by PrettyPrintable.
        """
        data = [
            (u"method", self.method),
            (u"url", self.url),
            (u"body", self.body),
            (u"headers", self.headers),
        ]
        return data

    def pretty_lines(self, pair_sep=": ", line_start="  "):
        # type: (Text, Text) -> List[Text]
        """Get a debug representation of attributes as a list of strings.

        This is really just used to customize the pretty_text() method provided
        by PrettyPrintable, so that each header gets its own line.
        """
        data = self.pretty_dict()
        for key in [u"body", u"headers"]:
            del data[key]
        lines = []
        for key, value in data.items():
            line = u"{0}{1}{2}".format(key, pair_sep, value)
            lines.append(line)
        lines.append(u"headers{0}".format(pair_sep))
        for key, value in self.headers.pairs():
            line = u"{0}{1}{2}{3}".format(line_start, key, pair_sep, value)
            lines.append(line)
        lines.append(u"body{0}".format(pair_sep))
        lines.append(u"{0}{1}".format(line_start, self.body))
        return lines
