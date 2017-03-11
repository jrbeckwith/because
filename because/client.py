"""Hold parameters and state for making any number of HTTP requests.
"""
import logging
from typing import (
    Any,
)
from . ssl_config import SSLConfig
from . request import Request
from . transfer import Transfer


LOG = logging.getLogger(__name__)



class Client(object):
    """Perform HTTP requests according to a described policy.
    
    Each instance of this class is effectively a bundle of parameters
    describing a policy for making HTTP requests, with methods for making
    requests according to that policy.

    Client collects a lot of parameters so that they can be passed and checked
    just once, as opposed to forcing users to save different things in a bunch
    of variables and repeatedly pass them all in different calls.

    A corollary of this is that, since an instance is meant to be reused any
    number of times, the state on a Client instance should generally be kept to
    a minimum, to avoid undesirable interference between requests (not to
    mention issues for concurrent implementations).
    
    Client should only contain data pertaining to performance of requests, but
    which are not individual to each request. Specifically, prospectively
    represented requests yet to be performed should be Requests, while
    per-connection state should be in Transfer.

    Client should encapsulate network I/O so that other code can be written in
    a way that is more deterministic and does not couple to the details of that
    I/O. For this reason, it is best if Client implementations are made small
    by extensive reuse of I/O-less components that are easier to test fully.
    """

    #: Default logger, used if no logger is passed for the log parameter.
    log = LOG.getChild("Client")

    #: Class called to make an SSLConfig if none was specified.
    #: Overriding this is a way of changing how SSL parameters are represented.
    ssl_config_cls = SSLConfig  # type: type

    # TODO: if an SSLConfig is passed that is of a different type from this, we
    # should convert to this to benefit from our own implementation.

    #: Class called to make a Transfer.
    #: Overriding this is a way of changing the implementation of how requests
    #: can be performed and managed asynchronously.
    transfer_cls = Transfer  # type: type

    def __init__(
            self,
            ssl_config=None,
            log=None,
    ):
        # type: (SSLConfig, logging.Logger) -> None
        """
        :arg ssl_config:
            To set the SSL configuration for all requests from this requester,
            pass an SSLConfig instance here.
        :arg log:
            logger to use, as per the Python logging module.
        """
        self.log = log or self.log

        # SSL config may need a ton of parameters, and typically none of them
        # are needed anyway, so we just take it whole and pass it on instead of
        # bloating the signature of __init__.
        # I know, "flat is better than nested," but for how many parameters?
        self.ssl_config = ssl_config or self.ssl_config_cls()

    def transfer(self, request, log=None):
        # type: (Request, logging.Logger) -> Any
        """Create a Transfer instance.
        """
        # The mediation of this method allows customizations in addition to
        # swapping out for a different transfer_cls.
        return self.transfer_cls(
            request=request,
            log=log,
        )

    def send(self, request):
        # type: (Request) -> Any
        """Start performing the given request and return a transfer.

        Ideally, this method does not block on the complete response, so that
        other work can be done, progress can be monitored, etc.
        """
        transfer = self.transfer(
            request=request,
            log=self.log,
        )
        transfer.start()
        return transfer
