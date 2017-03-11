"""Helpers for doing HTTP using SSL using the Python stdlib: ssl and httplib.
"""
import sys
import ssl
from typing import (
    Optional,
    Text,
)

from because.ssl_config import (
    InvalidSSLConfig,
    SSLKey as _SSLKey,
    SSLConfig as _SSLConfig,
)

# SSL/TLS versions
# (ssl.PROTOCOL_*)
# For now, don't offer a choice, see if anything else is needed
_PROTOCOL_CHOICES = {
    # Default option recommended in Python docs, but not avail < 2.7.13!
    # u"default": ssl.PROTOCOL_SSLv23,

    # same as PROTOCOL_TLS, deprecated in 3.6+
    # "ssl v2.3": ssl.PROTOCOL_SSLv23,

    # preferred alias only available in 3.6+
    # "tls": ssl.PROTOCOL_TLS,
}
# In 3.6+ the preferred name is PROTOCOL_TLS, try to avoid deprecated names here
if sys.version_info >= (3, 6):
    _PROTOCOL_CHOICES.update({
        u"default": ssl.PROTOCOL_TLS,
    })
# In 2.7 to 3.5, the available name is PROTOCOL_SSLv23
else:
    _PROTOCOL_CHOICES.update({
        u"default": ssl.PROTOCOL_SSLv23,
    })
_PROTOCOL_CHOICES_REVERSE = {
    value: key
    for key, value in _PROTOCOL_CHOICES.items()
}

# SSL Options
_PROTOCOL_OPTIONS = {
    # NOTE: inverted

    # this option wants OpenSSL 1.0.0+.
    "compression": ssl.OP_NO_COMPRESSION,

    "no ssl v2": ssl.OP_NO_SSLv2,
    "no ssl v3": ssl.OP_NO_SSLv3,
    "no tls v1": ssl.OP_NO_TLSv1,
    "no tls v1.1": ssl.OP_NO_TLSv1_1,
    "no tls v1.2": ssl.OP_NO_TLSv1_2,

    # NOTE: these not inverted (not _NO_WHATEVER). Also, only for server
    # sockets, but just to be scrupulous with defaults...
    "server cipher preference": ssl.OP_CIPHER_SERVER_PREFERENCE,
    "single dh use": ssl.OP_SINGLE_DH_USE,
    "single ecdh use": ssl.OP_SINGLE_ECDH_USE,
}
# All the options but these are inverted
_UNINVERTED_OPTIONS = set([
    "server cipher preference",
    "single dh use",
    "single ecdh use",
])
# 3.6+ exclusive options :(
if sys.version_info >= (3, 6):
    _PROTOCOL_OPTIONS.update({
    })


class SSLKey(_SSLKey):
    """httplib implementation of SSLKey.
    """
    # TODO: work out what uses keys and then have this provide what that needs


class SSLConfig(_SSLConfig):
    """httplib implementation of SSLConfig.
    """

    default_options = _SSLConfig.default_options.copy()
    default_options.update({
        # default options specific to this implementation go here.

        # after ssl.create_default_context default options.
        "compression": False,
        "server cipher preference": True,
        "single dh use": True,
        "single ecdh use": True,
    })

    def __init__(
            self,
            protocol=u"default",
            key=None,
            options=None,
    ):
        # type: (Text, Optional[SSLKey], Optional[dict]) -> None
        super(SSLConfig, self).__init__(
            protocol=protocol,
            key=key,
            options=options,
        )

        # Set up implementation-specific state...

        # If user didn't specify anything custom, use create_default_context
        # as the Python docs recommend to get what Python devs thought secure.
        if protocol == u"default" and not options:
            # "Passing SERVER_AUTH as purpose sets verify_mode to CERT_REQUIRED
            # and either loads CA certificates (when at least one of cafile,
            # capath or cadata is given) or uses
            # SSLContext.load_default_certs() to load default CA certificates."
            purpose = ssl.Purpose.SERVER_AUTH
            context = ssl.create_default_context(purpose)

        # Otherwise, the user wanted to specify their own stuff
        else:
            protocol_constant = _PROTOCOL_CHOICES.get(protocol)
            if protocol_constant is None:
                raise InvalidSSLConfig(
                    "unknown protocol for Python ssl: {0!r}".format(protocol)
                )
            # Only in 3.6+ this is created with secure default values.
            # That's why similar options are set in default_options
            context = ssl.SSLContext(protocol=protocol_constant)

            # Special case for mimicking create_default_context doc behavior
            if self.protocol != "ssl v2" and "no ssl v2" not in self.options:
                self.options["no ssl v2"] = True
            if self.protocol != "ssl v3" and "no ssl v3" not in self.options:
                self.options["no ssl v3"] = True

        self._context = context
        self._set_options()

    def _set_options(self):
        # type: () -> None
        """Internal: convert options to set QSSLConfiguration option flags.
        """

        # We can safely set options, but we can't safely unset them... so we
        # only have one shot to change these, otherwise just grab a new
        # context.

        for key, value in self.options.items():

            # Get the constant used by the ssl module
            option = _PROTOCOL_OPTIONS.get(key)

            # Make sure we don't fail silently with unrecognized options
            if option is None:
                raise InvalidSSLConfig(
                    "unknown option for Python ssl: {0!r}".format(key)
                )

            # option flags normally NO_WHATEVER, inverting the logic
            if key not in _UNINVERTED_OPTIONS:
                value = not value
            if value:
                self._context.options |= option

    def to_ssl_context(self):
        # type: () -> ssl.SSLContext
        return self._context
