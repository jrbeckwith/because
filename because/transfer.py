import logging
from typing import (
    Any,
    Optional,
    Callable,
    List,
    Text,
)
from datetime import (
    datetime as Datetime,
    timedelta as Timedelta,
)
from . errors import InvalidObject
from . future import Future
from . request import Request
from . response import Response
from . ssl_config import SSLConfig

LOG = logging.getLogger(__name__)


class TransferError(Exception):
    """Represents an error which happened while trying to execute a transfer.

    This should not represent HTTP errors, which are successful transfers that
    return valid Response objects (so caller can look at the specific code,
    look at the error body, etc.)

    This can be used as a base class for exceptions indicating more specific
    reasons why a good response couldn't be returned. However, problems in
    Response.__init__ should raise InvalidResponse instead.
    """
    # TODO: why not HTTP also? As long as the two aren't confused, that is.
    # I suppose the HTTP one is a property of the response instead.
    def __init__(self, text, code=None):
        # type: (Text, Optional[int]) -> None
        self.text = text
        self.code = code
        super(TransferError, self).__init__(text)


class InvalidTransfer(InvalidObject):
    """Raised instead of creating an invalid Transfer instance.
    """


class Transfer(Future):
    """Hold per-request state for one ongoing HTTP request cycle.

    This can play a role like a future or promise in implementations that
    support asynchronous network I/O.

    This can also be used as a device for bundling up multiple descriptions of
    a transfer's state to be handled by e.g. one callback, instead of requiring
    many separate callbacks to handle many different state notifications.
    """
    ssl_config_cls = SSLConfig  # type: type

    # n.b.: can't define signals here since this is not a QObject. The
    # workaround would be to have this instantiate a QObject subclass that
    # defines your signals. But the QNetworkReply already defines all the
    # signals we need here.

    #: Default logger to use if no logger was passed.
    log = LOG.getChild("Transfer")

    def __init__(self, request, ssl_config=None, log=None):
        # type: (Request, Optional[SSLConfig], logging.Logger) -> None
        """
        :arg request:
            Request object describing the HTTP request to be performed.
        :arg ssl_config:
            SSLConfig for the performance of the request.
        :arg log:
            logger instance to use for logging messages.
        """
        self.request = request                          # type: Request
        if not ssl_config:
            self.ssl_config = self.ssl_config_cls()     # type: SSLConfig
        else:
            self.ssl_config = ssl_config
        self.log = log or self.log                      # type: logging.Logger

        # Response produced
        self.response = None            # type: Response

        # Error produced instead of response
        # note: this may be used to refer to an internal exception, an HTTP
        # error code, or an application-level error indicated in the body.
        self.error = None               # type: Optional[TransferError]

        # Time the transfer was started, approximately
        self.started_at = None          # type: Datetime

        # Time the transfer was stopped, approximately
        self.stopped_at = None          # type: Datetime

        # Indicate whether the transfer was timed out
        self.timed_out = None           # type: bool

    def start(self):
        # type: () -> None
        """Begin the transfer.

        This method allows execution of a transfer to be deferred after its
        construction, which couldn't be done if __init__ started it.
        """
        self.started_at = Datetime.utcnow()

    def result(self):
        # This should raise if anything happened.

        # Base class has nothing useful to return.
        return None

    def wait(self):
        # type: () -> Response
        """Block until the transfer is finished, then give a result.

        Returns a Response or raises a TransferError.
        """
        self.stopped_at = Datetime.utcnow()

        # Normally we'd block here, but this base class has no way to block,
        # and nothing to block on. Subclasses should do something here.

        # NOTE: this call should probably raise if we got an exception.
        return self.result()

    def cancel(self):
        """Cancel ongoing work and abort the transfer.
        """
        # Time roughly when the transfer stopped, for logging purposes
        self.stopped_at = Datetime.utcnow()

        # This should return True if anything was actually cancelled.
        return False

    def close(self):
        # type: () -> None
        """Cancel ongoing work, clean up state and disable the instance.
        """
        # Ensure nothing is still in process when we clean up.
        self.cancel()

    def duration(self):
        # type: () -> float
        """Compute the duration of the transfer, in seconds.

        If the transfer has not started, this returns 0. If the transfer is
        still ongoing, this returns how much time has elapsed so far.
        """
        if not self.started_at:
            timedelta = Timedelta()
        else:
            latest = self.stopped_at or Datetime.utcnow()
            timedelta = latest - self.started_at
        return timedelta.total_seconds()

    def __enter__(self):
        # type: () -> Transfer
        return self

    def __exit__(self, type_, value, traceback):
        # type: (type, Exception, Any) -> None
        self.close()
