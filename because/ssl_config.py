"""Base classes for interfaces offering HTTP over SSL or TLS.

This arises as a way of mitigating the huge number of parameters that some HTTP
APIs offer for customizing the behavior of TLS/SSL. Instead of passing 43
arguments to Client, you can just pass whichever ones apply to your
implementation to your implementation's flavor of SSLConfig, and pass that to
the Client so I can pretend that Client is simpler than it is.
"""
from . errors import InvalidObject
from typing import Text


class InvalidSSLConfig(InvalidObject):
    """Raised when SSL configuration was specified that won't be understood.
    """
    pass


class SSLKey(object):
    """Represent a key used in an SSL or TLS configuration.

    This is partly here to provide a place to put parameters like algorithm,
    key encoding, and key type, if they are ever needed by a particular
    implementation.
    """

    def __init__(self, data, pass_phrase=b""):
        # type: (bytes, bytes) -> None

        self.data = data
        self.pass_phrase = pass_phrase


class SSLConfig(object):
    """Parameters for setting up whatever SSL configuration is needed.

    Each implementation offers its own SSLConfig to take care of the details,
    hide the dance of working with keys, make it easier to set options,
    and use secure defaults.
    """

    #: Default options to set in this implementation.
    #: These should be plain Python types, not implementation-specific types,
    #: but otherwise can be arbitrary.
    default_options = {
        # Disable TLS compression to prevent CRIME session hijacking.
        # Many browsers never supported it anyway, new FF/Chrome disable it
        # e.g. ssl.OP_NO_COMPRESSION, QSsl.SslOptionDisableCompression
        "compression": False,
    }

    def __init__(
            self,
            protocol="default",
            key=None,
            options=None,
    ):
        # type: (Text, SSLKey, dict) -> None

        self.protocol = protocol or "default"
        self.key = key

        # Make a defensive copy of defaults, then override them from the arg
        self.options = self.default_options.copy()
        if options is not None:
            self.options.update(options)
