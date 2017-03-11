"""This module is a place for code which customizes a BCS service definition.
"""

import json
import base64
from datetime import datetime
import collections
from typing import Text
from because.response import parse_json
from because.errors import ParseError, InvalidObject
from because.headers import Headers
from because.services.headers import DEFAULT_HEADERS
from because.service import (
    Service,
    Endpoint,
)
from because.reprs import ReprMixin
from because.pretty import PrettyMixin


def parse_token_response(response):
    data = parse_json(response, ["token"])
    if not data:
        raise ParseError(
            "token response body JSON represents an empty object"
        )
    return data


def parse_token_response_dict(data, response=None):
    text = data.get("token")
    if not text:
        if "token" not in data:
            raise ParseError(
                "token dict does not contain 'token' key",
                response=response,
            )
        raise ParseError(
            "token dict does not contain value for 'token' key",
            response=response,
        )
    return text


def encode_token_text(text, response=None):
    # Why hardcode this encoding?
    # JSON is required to use utf-8. While the python JSON package uses
    # Text to represent this data, it should always encode as utf-8.
    # Moreover, token should be base64, utf-8 is more than enough there.
    # If it isn't, then we actually want a traceback, not another encoding.
    try:
        blob = text.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ParseError(
            "token blob cannot be encoded as utf-8",
            error=error, response=response,
        )
    return blob


def parse_token_blob(blob, response=None):
    parts = blob.split(b".", 2)
    if len(parts) < 2:
        raise ParseError(
            "cannot parse token blob into parts",
            response=response,
        )
    middle = parts[1]
    padding = (len(middle) % 4) * b"="
    payload = base64.b64decode(middle + padding)
    # Reminder: JSON is required to be utf-8, we want to fail if it's not
    try:
        decoded = payload.decode("utf-8")
        data = json.loads(decoded)
    except (UnicodeDecodeError, ValueError, TypeError) as error:
        raise ParseError(
            "Could not parse decoded token blob as JSON",
            response=response,
            error=error,
        )
    return data


class InvalidToken(InvalidObject):
    """Raised instead of creating an invalid Token instance.
    """


class Token(ReprMixin, PrettyMixin):
    """Represent a token (JWT) obtained from the token service.
    """

    # Shared definition, avoid reflection magic making mysteries
    attrs = collections.OrderedDict([
        ("name", "name"),
        ("email", "email"),
        ("email_verified", "email_verified"),
        ("roles", None),
        ("audience", "aud"),
        ("subject", "sub"),
        ("issuer", "iss"),
        ("issued_at", "iat"),
        ("expiration", "exp"),
    ])

    def __init__(
            self,
            name,
            email,
            email_verified,
            audience,
            subject,
            issuer,
            issued_at,
            expiration,
            roles=None,
            encoded=None,
    ):
        """
        :arg name:
            An identifying string, like a full name, but just as likely to be
            the email address.
        :arg email:
            An email address for the user.
        :arg email_verified:
            A flag indicating if the user's email address was verified.
        :arg audience:
            Opaque string that "identifies the recipients that the JWT is
            intended for."
        :arg subject:
            String that "identifies the principal that is the subject of the
            JWT."
        :arg issuer:
            String that "identifies the principal that issued the JWT."
        :arg issued_at:
            Datetime representing when the JWT was issued.
        :arg expiration:
            Datetime representing when the JWT expires.
        :arg roles:
            A sequence of strings identifying roles the user has.
        :arg encoded:
            Raw form of the token, suitable for sending on.
        """
        self.name = name
        self.email = email
        self.email_verified = email_verified
        if isinstance(roles, (bytes, Text)):
            raise InvalidToken("roles must be a sequence, not a string")
        self.roles = frozenset(roles or [])
        self.audience = audience
        self.issued_at = issued_at
        self.subject = subject
        self.issuer = issuer
        self.expiration = expiration
        self.encoded = encoded

    def __eq__(self, other):
        # type: (Any) -> bool
        """Compare two instances for equality.
        """
        return all(
            getattr(self, attr) == getattr(other, attr)
            for attr in type(self).attrs.keys()
        )

    def pretty_tuples(self):
        """Internal: for use with PrettyMixin to get .pretty_text().
        """
        return [
            (attr, getattr(self, attr))
            for attr in type(self).attrs.keys()
        ]

    def repr_data(self):
        """Internal: for use with ReprMixin.
        """
        return collections.OrderedDict(self.pretty_tuples())

    @classmethod
    def from_response(cls, response):
        """Turn a token service response into a Token.
        """
        data = parse_token_response(response)
        text = parse_token_response_dict(data, response=response)
        blob = encode_token_text(text, response=response)
        return cls.from_bytes(blob)

    @classmethod
    def from_bytes(cls, blob, response=None):
        """Turn the token blob into a Token.
        """
        data = parse_token_blob(blob, response=response)

        # At this point an error is no longer a parse issue, it's constructor
        # validation issues, so we don't keep passing response to ensure parse
        # errors are linked to the response.
        return cls.from_data(data, encoded=blob)

    @classmethod
    def from_data(cls, data, encoded=None):
        """Turn an object (like a decoded token blob) into a Token.
        """
        copied = data.copy()
        app_metadata = copied.get("app_metadata")
        roles = app_metadata.get("SiteRole").split(",")
        del copied["app_metadata"]

        date_keys = ["exp", "iat"]
        dates = {}
        for key in date_keys:
            value = copied.get(key)
            if value:
                dates[key] = datetime.utcfromtimestamp(value)
        copied.update(dates)

        mapped = {
            key: (copied[value] if value else None)
            for key, value in cls.attrs.items()
        }
        mapped["roles"] = roles
        mapped["encoded"] = encoded
        return cls(**mapped)

    def as_text(self):
        return self.encoded.decode("utf-8") if self.encoded else u""


class TokenService(Service):
    """Define endpoints for BCS token service.
    """
    def __init__(self):
        # type: () -> None
        endpoints = {
            # send credentials, receive Auth0 token for headers
            u"token": Endpoint(
                path=u"/token/",
                methods=[u"POST"],
                parameters={
                    # body parameters currently not used...
                    # "username": Text,
                    # "password": Text,
                }

            ),
        }
        headers = Headers.merged(
            DEFAULT_HEADERS,
            Headers.coerce([
                (b"Content-Type", b"application/json"),
            ])
        )
        super(TokenService, self).__init__(
            endpoints,
            headers=headers,
        )

    def login_request(self, base, username, password, headers=None):

        body = json.dumps({
            u"username": username,
            u"password": password,
        }).encode("utf-8")

        return self.request(
            endpoint_name=u"token", method=u"POST", base=base, body=body,
            headers=headers,
        )

    def parse(self, response):
        return Token.from_response(response)
