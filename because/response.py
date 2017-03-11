import json
import collections
from typing import (
    Any,
    Optional,
    Tuple,
    List,
    Text,
)
from . reprs import ReprMixin
from . pretty import PrettyMixin
from . errors import InvalidObject, ParseError
from . headers import Headers


class InvalidResponse(InvalidObject):
    """Raised instead of creating an invalid Response instance.
    """


class Response(ReprMixin, PrettyMixin):
    """Represent a received HTTP response.

    You may be saying to yourself: "why yet another class Response?!?" Well --
    this internal representation is used to abstract over representations like
    httplib.HTTPResponse or QNetworkReply, so that `because` can work about the
    same in multiple environments without all the response processing code
    having to be duplicated with minor variations in it.
    """
    def __init__(self, status, headers=None, body=b""):
        # type: (int, Optional[Any], Optional[bytes]) -> None
        """
        :arg status:
            HTTP response status code
        :arg headers:
            HTTP response headers 
        :arg body:
            HTTP response body, as a bytestring
        """
        self.status = self._init_status(status)     # type: int
        self.body = self._init_body(body)           # type: Optional[bytes]
        self.headers = self._init_headers(headers)  # type: Headers

    def _init_status(self, value):
        # type: (int) -> int
        # TODO: I have trouble committing to a status repr type
        if not isinstance(value, int):
            raise InvalidResponse("status must be int")
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

    def _init_body(self, value):
        # type: (Optional[bytes]) -> Optional[bytes]
        if value is not None and not isinstance(value, bytes):
            raise InvalidResponse("body must be bytes")
        return value

    def __eq__(self, other):
        # type: (Any) -> bool
        """Compare two instances for equality.
        """
        attrs = ["status", "headers", "body"]
        return all(
            getattr(self, attr) == getattr(other, attr)
            for attr in attrs
        )

    def repr_data(self):
        return collections.OrderedDict([
            ("status", self.status),
            ("headers", list(self.headers.pairs())),
            ("body", self.body),
        ])

    def pretty_tuples(self):
        # type: () -> List[Tuple[Text, Any]]
        """Get a debug representation of attributes as a list of tuples.

        This is really just used to customize the pretty_text() method provided
        by PrettyMixin.
        """
        return [
            (u"status", self.status),
            (u"headers", self.headers),
            (u"body", self.body),
        ]

    def pretty_lines(self, pair_sep=u": ", line_start=u"  "):
        # type: (Text, Text) -> List[Text]
        """Get a debug representation of attributes as a list of strings.

        This is really just used to customize the pretty_text() method provided
        by PrettyMixin, so that each header gets its own line.
        """
        data = self.pretty_dict()
        for key in [u"body", u"headers"]:
            del data[key]
        lines = []
        for key, value in data.items():
            line = u"{0}{1}{2}".format(key, pair_sep, value)
            lines.append(line)
        lines.append("headers{0}".format(pair_sep))
        for key, value in self.headers.pairs():
            line = u"{0}{1}{2}{3}".format(line_start, key, pair_sep, value)
            lines.append(line)
        lines.append(u"body{0}".format(pair_sep))
        lines.append(u"{0}{1}".format(line_start, self.body))
        return lines


def parse_json(response, required_keys=None):
    # type: (Response, List[Text]) -> dict[Text, Any]
    """Parse the given response object as JSON, returning data.

    The advantage of using this is that it does all the customary pre-checks on
    the response, raising ParseError for any that fail. Callers would therefore
    be advised to handle these exceptions in whatever way was appropriate to
    the context.

    :arg response:
        The response to parse.
    :arg caller:
        If supplied, this should be the service object doing the parse, to help
        with debugging.
    """

    if not response:
        raise ParseError(
            "response was falsy",
            response=response,
        )

    if response.status != 200:
        raise ParseError(
            "response had error status {0!r}".format(response.status),
            response=response,
        )

    blob = response.body
    if not blob:
        raise ParseError(
            "response had empty body",
            response=response,
        )

    try:
        # JSON requires utf-8, so this hardcoding is judicious
        text = blob.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ParseError(
            "cannot decode bytes in response body as utf-8",
            response=response,
            error=error,
        )

    try:
        data = json.loads(text)
    # n.b.: JSONDecodeError, in Python 3 only, subclasses of ValueError.
    except ValueError as error:
        raise ParseError(
            "cannot decode response body as JSON",
            response=response,
            error=error,
        )

    # Look for known error body form
    if isinstance(data, dict) and data.get("error"):
        raise ParseError(
            "response body indicates an error occurred: {0!r}"
            .format(data.get("error")),
            response=response,
        )

    if required_keys:
        missing_keys = sorted([
            key for key in required_keys
            if key not in data
        ])
        if missing_keys:
            raise ParseError(
                "JSON response missing required keys: {0!r}"
                .format(missing_keys),
                response=response,
            )

    return data
