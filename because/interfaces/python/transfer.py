import logging
from collections import OrderedDict
from datetime import datetime as Datetime
from typing import (
    Any,
    Union,
    Optional,
    Tuple,
    List,
    Text,
    Callable,
)

import ssl
try:
    import http.client as httplib
except ImportError:
    import httplib  # type: ignore
try:
    import urllib.parse
    from urllib.parse import ParseResult
    URLPARSE = urllib.parse
except ImportError:
    import urlparse
    from urlparse import ParseResult
    URLPARSE = urlparse


from because.errors import InvalidObject
from because.request import Request
from because.response import Response
from because.headers import Headers
from because.transfer import (
    InvalidTransfer,
    TransferError,
    Transfer as _Transfer,
)
from because.interfaces.python.ssl_config import SSLConfig

# mypy, you are wrong and I'll prove it, look:
assert hasattr(SSLConfig, "to_ssl_context")

LOG = logging.getLogger(__name__)


class Transfer(_Transfer):
    """Blocking implementation of Transfer using httplib.

    Because this implementation blocks, start() is a no-op, and all the real
    work happens in wait(). Since there is no reason to defer cleanup, close()
    is also a no-op.
    """

    # n.b.: can't define signals here since this is not a QObject. The
    # workaround would be to have this instantiate a QObject subclass that
    # defines your signals. But the QNetworkReply already defines all the
    # signals we need here.

    log = LOG.getChild("Transfer")

    def __init__(
            self,
            request,            # type: Request
            ssl_config=None,    # type: SSLConfig
            log=None,           # type: logging.Logger
    ):
        # type: (...) -> None
        """
        :arg request:
            Request object describing the HTTP request to be performed.
        :arg log:
            logger instance to use for logging messages.
        """
        # Store passed parameters
        self.request = request
        self.ssl_config = ssl_config or SSLConfig()
        self.log = log or self.log

        # Initialize internal state
        self.response = None                         # type: Optional[Response]

    def wait(self):
        # type: () -> Response
        """Block until transfer is finished, then return a Response.

        In this implementation, all the work is done in this method.
        """
        return self._get_response(self.request)

    def _get_method_url_body(self, request, encoding="utf-8"):
        # type: (Request, str) -> Tuple[Text, Text, Optional[Text]]
        """Start unpacking request for consumption by httplib.
        """
        # Guarantee method and url are text if we didn't raise
        if not request.method or not request.url:
            raise InvalidTransfer("invalid method or url")
        # If value is bytes, return text. If it is None, return None.
        method, url, body = (
            value.decode(encoding) if isinstance(value, bytes) else value
            for value in [request.method, request.url, request.body]
        )
        return method, url, body

    def _get_connection(self, parsed):
        # type: (ParseResult) -> httplib.HTTPConnection
        """Get an HTTPConnection instance appropriate to the parsed URL.
        """
        if parsed.scheme == "http":
            connection = httplib.HTTPConnection(
                host=parsed.hostname, port=parsed.port,
            )
        elif parsed.scheme == "https":
            assert hasattr(self.ssl_config, "to_ssl_context")
            context = self.ssl_config.to_ssl_context()
            connection = httplib.HTTPSConnection(
                host=parsed.hostname, port=parsed.port, context=context,
            )
        else:
            raise InvalidTransfer(
                "unrecognized scheme {0!r}".format(parsed.scheme)
            )
        return connection

    def _get_headers(self, request):
        # type: (Request) -> OrderedDict
        """Convert the request headers into a form that httplib likes.
        """
        # connection.request needs a mapping of one key to one value, so we use
        # combined_pairs to squash values together. To try to preserve ordering
        # as it iterates over headers, we pass OrderedDict.
        return OrderedDict(request.headers.combined_pairs())

    def _get_uri(self, parsed):
        # reconstruct relative path + query from pieces given by urlparse
        # (despite the parameter name, connection.request url isn't absolute)
        return parsed.path + ("?" + parsed.query if parsed.query else "")

    def _decode_headers(self, httplib_headers, encoding="utf-8"):
        if not bool(httplib_headers):
            return httplib_headers
        first_pair = httplib_headers[0]
        first_pair_key = first_pair[0]
        if isinstance(first_pair_key, bytes):
            return httplib_headers
        return [
                (key.encode(encoding), value.encode(encoding))
                for key, value in httplib_headers
            ]

    def _decode_body(self, body):
        # type: (str) -> bytes
        if not isinstance(body, bytes):
            return body.encode("utf-8")
        return body

    def _get_response(self, request):
        # type: (Request) -> Response

        # httplib hardcodes str literals: bytes in Python 2, text in Python 3.
        # So we have to split on str literals.
        # So the url arg we pass to httplib has to be str.

        method, url, body = self._get_method_url_body(request)
        headers = self._get_headers(request)
        parsed = URLPARSE.urlparse(url)
        connection = self._get_connection(parsed)
        uri = self._get_uri(parsed)

        # Actually start it, and block until it finishes.
        # This returns None - response must be obtained from connection itself
        connection.request(method=method, url=uri, headers=headers, body=body)

        # Collect and repack as Response for backend-agnostic consumers.
        httplib_response = connection.getresponse()
        status = httplib_response.status
        headers_bytes = self._decode_headers(httplib_response.getheaders())

        # TODO: the whole response is read into memory here, not ideal
        raw = httplib_response.read()
        decoded = self._decode_body(raw)

        # NOTE: "Note that you must have read the whole response before you can
        # send a new request to the server." Not sure if this only applies to
        # reuse of the same HTTPConnection object, which we don't do anyway.

        response = Response(
            status=status,
            headers=headers_bytes,
            body=decoded,
        )
        return response
