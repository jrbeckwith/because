"""Helpers for doing HTTP using SSL using PyQt APIs.
"""
from typing import Text

# HTTP backend
try:
    from PyQt5.QtNetwork import (
        QSsl,
        QSslKey,
        QSslConfiguration,
    )
except ImportError:
    from PyQt4.QtNetwork import (
        QSsl,
        QSslKey,
        QSslConfiguration,
    )

from because.ssl_config import (
    InvalidSSLConfig,
    SSLKey as _SSLKey,
    SSLConfig as _SSLConfig,
)

# SSL/TLS versions
# (QSsl.SslProtocol)
# For now, don't offer a choice, see if anything else is needed
_PROTOCOL_CHOICES = {
    # Default option recommended in Qt docs
    u"default": QSsl.SecureProtocols,

    # Deprecated options
    # u"ssl v2": QSsl.SslV2,
    # u"ssl v3": QSsl.SslV3,
    # u"tls v1.0": QSsl.TlsV1_0,
    # u"tls v1.1": QSsl.TlsV1_1,
    # u"tls v1.2": QSsl.TlsV1_2,
}

# SSL Options
# (QSsl.SslOption)
_PROTOCOL_OPTIONS = {
    # n.b.: these are all inverted
    u"empty fragments": QSsl.SslOptionDisableEmptyFragments,
    u"session tickets": QSsl.SslOptionDisableSessionTickets,
    # like ssl.OP_NO_COMPRESSION
    u"compression": QSsl.SslOptionDisableCompression,
    u"server name indication": QSsl.SslOptionDisableServerNameIndication,
    u"legacy renegotiation": QSsl.SslOptionDisableLegacyRenegotiation,
}


class SSLKey(_SSLKey):
    """Qt-convertable implementation of SSLKey.
    """

    def __init__(self, data, pass_phrase=b""):
        # type: (bytes, bytes) -> None

        # While I'm checking type annotations, callers might not be.
        # While duck types are great, PyQt handles them very poorly.
        # It's worth a couple isinstance checks to avoid the segfaults and
        # provide diagnostic information.

        if not isinstance(data, bytes):
            raise InvalidSSLConfig(
                u"encoded key data must be bytes"
            )

        self.data = data

        if not isinstance(pass_phrase, bytes):
            raise InvalidSSLConfig(
                u"pass phrase must be bytes"
            )
        self.pass_phrase = pass_phrase

    def to_q_ssl_key(self):
        """Return a QSslKey.

        This assumes certain defaults.
        """
        # DSA is rarely seen and has no equivalent in httplib.
        q_algorithm = QSsl.Rsa  # type: QSsl.KeyAlgorithm

        # httplib only seems to use PEM and I haven't used DER
        q_encoding = QSsl.Pem  # type: QSsl.EncodingFormat

        q_key_type = QSsl.PrivateKey  # type: QSsl.KeyType
        # q_key_type = QSsl.PublicKey  # type: QSsl.KeyType

        return QSslKey(
            self.data, q_algorithm, q_encoding, q_key_type, self.pass_phrase,
        )


class SSLConfig(_SSLConfig):
    """Qt-based implementation of SSLConfig.

    This implementation does a few things to help:

    * Automate QSslConfiguration.set* calls and ensure that they happen up
      front, which is important when some may have no effect later.

    * Hide the dance of creating a QSslKey.

    * Makes it easier to set SSL options, and sets defaults marked in Qt docs
      as more secure, so that less secure options must be explicitly specified.
    """

    default_options = _SSLConfig.default_options.copy()
    default_options.update({
        # Prevent injection of plaintext into SSL sessions.
        # This option isn't available for other backends.
        "legacy renegotiation": False,

        # Prevents BEAST, but "causes problems with a large number of servers".
        # Yet it works with BCS, so we should use it when it's available.
        "empty_fragments": False,
    })

    def __init__(
            self,
            protocol=None,
            key=None,
            options=None,
    ):
        super(SSLConfig, self).__init__(
            protocol=protocol,
            key=key,
            options=options,
        )

        # Set up implementation-specific state...

        # QSslConfiguration is a bag of data we need to talk to Qt. Its
        # attributes must be set using its various setWhatever methods.
        self._q_ssl_config = QSslConfiguration()

        # Get a protocol constant Qt understands, or cry to the user.
        q_ssl_protocol = _PROTOCOL_CHOICES.get(self.protocol)
        if q_ssl_protocol is None:
            raise InvalidSSLConfig(
                "unknown protocol for Qt: {0!r}".format(self.protocol)
            )
        # Hang on to it just in case we possibly need it, e.g. debugger
        self._q_ssl_protocol = q_ssl_protocol
    
        # Otherwise, tell Qt about the protocol.
        # n.b.: setting this after connection starts has no effect, so we
        # definitely want to do it here instead of deferring this.
        self._q_ssl_config.setProtocol(q_ssl_protocol)

        # If we have an SSLKey, have it make a QSslKey and tell Qt about it.
        if self.key:
            q_ssl_key = self.key.to_q_ssl_key()
            self._q_ssl_config.setPrivateKey(q_ssl_key)
        else:
            q_ssl_key = None
        self._q_ssl_key = q_ssl_key

        # Process self.options
        self._set_options()

    def _set_options(self):
        """Internal: convert options to set QSSLConfiguration option flags.
        """
        for key, value in self.options.items():

            # Get the constant used by PyQt
            option = _PROTOCOL_OPTIONS.get(key.lower().replace("_", " "))

            # Make sure we don't fail silently with unrecognized options
            if option is None:
                raise InvalidSSLConfig(
                    "unknown option for Qt: {0!r}".format(key)
                )

            # All the Qt options are "Disable*", inverting the bools.
            self._q_ssl_config.setSslOption(option, not value)
