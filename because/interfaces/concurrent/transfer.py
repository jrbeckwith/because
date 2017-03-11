# TODO: this should just sit on top of the blocking impl
# TODO: maybe don't use httplib directly?

import logging
from datetime import datetime as Datetime
from typing import (
    Any,
    Union,
    Optional,
    Tuple,
    List,
    Text,
)

import asyncio
import ssl
try:
    import http.client as httplib
except ImportError:
    import httplib  # type: ignore
try:
    import urllib.parse
    URLPARSE = urllib.parse
except ImportError:
    import urlparse
    URLPARSE = urlparse


from because.errors import InvalidObject
from because.request import Request
from because.response import Response
from because.headers import Headers
from because.transfer import Transfer as _Transfer, InvalidTransfer
from because.interfaces.python.ssl_config import SSLConfig

LOG = logging.getLogger(__name__)


def _connection(url, ssl_config):
    parsed = URLPARSE.urlparse(url)

    if parsed.scheme == "http":
        connection = httplib.HTTPConnection(
            host=parsed.hostname,
            port=parsed.port,
        )
    elif parsed.scheme == "https":
        context = ssl_config.to_ssl_context()  # type: ssl.SSLContext
        connection = httplib.HTTPSConnection(
            host=parsed.hostname,
            port=parsed.port,
            context=context,
        )
    else:
        raise Exception("fixme")

    return connection, parsed


def _get_response(request, ssl_config):
    # The implementaton of httplib (aka http.client) hardcodes the use
    # of str literals, which are bytes in Python 2 and text in Python 3.
    # So we have to split on str literals, which means url HAS to be str.
    # We can do this decode provided that url is always internally
    # generated and always encoded in utf-8.
    # TODO: maybe don't decode, just always store as Text? :/

    def coerce(value):
        # type: (Optional[Union[Text, bytes]]) -> Optional[Text]
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return value

    method, url, body = (
        coerce(item) for item in (
            request.method,
            request.url,
            request.body,
        )
    )

    # Hold on to connection so we can get data later
    # TODO: signature's all messed up here
    connection, parsed = _connection(url=url, ssl_config=ssl_config)

    # ugh, connection.request wants a dict?
    headers = dict(request.headers.pairs())

    connection.request(
        method=method,
        # TODO: query, fragment?
        url=parsed.path + ("?" + parsed.query if parsed.query else ""),
        headers=headers,
        body=body,
    )
    _response = connection.getresponse()
    headers_str = _response.getheaders()
    if bool(headers_str) and not isinstance(headers_str[0][0], bytes):
        encoding = "utf-8"
        headers_bytes = [
            (key.encode(encoding), value.encode(encoding))
            for key, value in headers_str
        ]
    else:
        headers_bytes = headers_str
    # TODO: the whole response is read into memory...
    body = _response.read()

    # Repack for internal consumers which don't assume httplib was used.
    # TODO: shouldn't have to manually create Headers?
    status = _response.status

    response = Response(
        status=status,
        headers=headers_bytes,
        body=body,
    )
    return response


class Transfer(_Transfer):
    ssl_config_cls = SSLConfig

    log = LOG.getChild("Transfer")

    def __init__(
            self, request, ssl_config=None, log=None,
            _executor=None, _loop=None,
    ):
        self._executor = _executor
        self._loop = _loop

        self._future = None
        super(Transfer, self).__init__(
            request=request,
            ssl_config=ssl_config,
            log=log,
        )

    # TODO: ensure that the callable submitted to executor is entirely
    # serializable.

    def start(self):
        # type: () -> Any
        """Begin the transfer.

        This method allows execution of a transfer to be deferred after its
        construction.
        """
        # Already started
        if self._future:
            return

        if not self.request.url:
            raise InvalidTransfer("falsy url")

        self._future = self._executor.submit(
            _get_response, request=self.request, ssl_config=self.ssl_config,
        )

    def cancel(self):
        if self._future:
            return self._future.cancel()

    def _done(self):
        """What to do after we're done waiting.
        """
        # If the future is done, e.g. from __await__, getting its result won't
        # block. Otherwise, it will block until request + processing is done.
        # Put it on self so any holder of this instance can get it later.
        self.response = self._future.result()

        # Make the response available as in 'response = await transfer'.
        return self.response

    def __iter__(self):
        # This impl can be used without an asyncio event loop.
        pass

    def __await__(self):
        # This impl assumes we are in Python 3, where "yield from" parses and
        # we have asyncio, but there shouldn't be many concurrent.futures users
        # who don't have such a Python 3 anyway...

        # Start if we didn't start already
        self.start()

        # Wrap concurrent.futures.Future and ask asyncio's loop to wake us up
        # when it's done, without blocking.
        yield from asyncio.wrap_future(self._future, loop=self._loop)

        response = self._done()
        return response

    def wait(self):
        # This should already be started for blocking users, but just in case,
        # since we'll crash if we happen not to have self.future yet.
        self.start()

        # This will block.
        return self._done()
