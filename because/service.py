"""Store specifications of how to access services.
"""
from typing import (
    Any,
    Optional,
    Sequence,
    List,
    Set,
    FrozenSet,
    Text,
)
try:
    import urllib.parse
    quote = urllib.parse.quote
except ImportError:
    import urllib
    quote = urllib.quote

from . errors import InvalidObject
from . headers import Headers
from . request import Request


class InvalidEndpoint(InvalidObject):
    """
    """


class UnknownEndpoint(Exception):
    """The given endpoint name is not known, preventing construction of a URL.
    """


class URLError(Exception):
    """Insufficient or valid information to build an endpoint URL.
    """


class Service(object):
    """Describe how to interact with a collection of related endpoints.

    :note: This interface is still in flux and still has some wrinkles.

    Instances of this class store invariant parameters that are not expected to
    change. It doesn't matter if arguments are loaded from config files,
    specified in Python modules, discovered by other requests, etc.

    Base URLs are specified separately at the time URLs or requests are
    generated. This allows the same service definition to be used against
    different deployments, e.g. test vs. prod.
    
    Associate and hold information on a collection of related endpoints.
    """

    def __init__(self, endpoints, headers=None, base=None):
        # type: (dict[Text, Endpoint], Optional[Headers], Any) -> None
        """
        :arg endpoints:
            dict (or similar object) mapping names to Endpoint instances to be
            grouped together under this service.
        :arg headers:
            Optional. Default HTTP headers to use in requests constructed
            through this service. In cases of conflicting headers, these will
            be overridden by headers specified by the endpoint or host.
        :arg base:
            Optional. Base URL, prefixed to all endpoint URIs.
        """
        self.endpoints = endpoints
        self._headers = headers or Headers()
        self.base = base

    def endpoint(self, endpoint_name):
        # type: (Text) -> Endpoint
        try:
            endpoint = self.endpoints[endpoint_name]
        except KeyError:
            raise UnknownEndpoint(endpoint_name)
        return endpoint

    def url(self, endpoint_name, base=None, values=None):
        # type: (Text, Text, Optional[dict[Text, Text]]) -> Text
        """Generate a URL to be used in a request to this service.

        :arg base:
            Base URL to use. If a base URL was supplied to the service
            instance, this parameter overrides that. Otherwise, this
            parameters supplies it.
        """
        base = base or self.base
        if not base:
            raise URLError(
                "specify a base URL for the service or in the url() call."
            )
        # blegh
        if isinstance(base, bytes):
            base = base.decode("utf-8")

        endpoint = self.endpoint(endpoint_name)
        result = endpoint.url(base=base, values=values)
        return result

    def headers(self):
        # type: () -> Headers
        """Generate headers to be used in a request to this service.
        """
        new = self._headers.copy()  # type: Headers
        return new

    def request(self, endpoint_name, method, base, values=None, body=None,
                headers=None):
        # type: (Text, Text, Text, Optional[dict], Optional[bytes], Optional[Headers]) -> Request
        """Generate a description of an HTTP request.

        This method can be overridden to customize generated requests for a
        particular kind of service.
        """
        # The endpoint can do the bulk of the request construction,
        # but it needs to provide default headers that request overrides
        endpoint = self.endpoint(endpoint_name)
        request = endpoint.request(
            method, base=base, values=values, body=body, headers=headers,
        )
        request.headers = Headers.merged(self._headers, request.headers)
        return request


class Endpoint(object):
    """Describe how to interact with a single endpoint.

    :note: This interface is still in flux and still has some wrinkles.

    Here, an endpoint is defined as a consistent form for relative URIs,
    representable as a template containing placeholders. This is associated
    with information on how to compose requests against those relative URIs.

    Base URLs are specified separately, allowing the same endpoint definition
    to be used against different deployments, e.g. test vs. prod.
    """
    def __init__(
            self,
            path,               # type: Text
            query=None,         # type: Optional[Text]
            parameters=None,    # type: Optional[dict[Text, Any]]
            methods=None,       # type: Optional[List[Text]]
            headers=None        # type: Optional[Headers]
    ):
        # type: (...) -> None
        """
        :arg path:
            A template for constructing relative URIs, as a format string
            (str.format). This should not include the query. The query should
            be specified separately.
        :arg query:
            A template for constructing the query.
        :arg parameters:
            Dict mapping names of parameters in the path template to Parameter
            objects describing their type. This defines how to fill in the
            template.
        :arg methods:
            ? Sequence of HTTP methods supported by this endpoint.
        :arg headers:
            Optional. Default HTTP headers to use in requests to this endpoint.
        """
        # Find obvious typos
        if not path.startswith("/"):
            raise InvalidEndpoint(
                "path does not start with '/': {0!r}"
                .format(path)
            )
        self.path = path
        if "?" in path:
            raise InvalidEndpoint(
                "path contains ?, use the query parameter instead: {0!r}"
                .format(path)
            )
        self.query = query
        self.parameters = parameters or {}
        self.methods = methods or []
        self._headers = headers or Headers()

    def uri(self, values=None):
        # type: (Optional[dict[Text, Any]]) -> Text
        """Generate a relative URI that can be appended to a base URL.

        :arg values:
            Dictionary of values for the template.
        """
        if values is None:
            values = {}

        # Check args against parameter types before liftoff
        for key, arg in values.items():
            expected_type = self.parameters[key]

            # expectation was communicated as a set of values
            if isinstance(expected_type, (Set, FrozenSet)):
                if arg not in expected_type:
                    raise URLError(
                        "invalid value for arg {0}: got {1}, expected {2}"
                        .format(key, arg, expected_type)
                    )

            # expectation was communicated as a type
            elif not isinstance(arg, expected_type):
                raise URLError(
                    "invalid type for arg {0}: got {1} of {2}, expected {3}"
                    .format(key, arg, type(arg), expected_type)
                )

        # Build a dict of args suitable for str.format()
        converted = {}
        for key, arg in values.items():
            value = None
            if isinstance(arg, int):
                value = str(arg)
            elif isinstance(arg, bytes):
                value = arg.decode("utf-8")
            else:
                # ugh
                value = str(arg)
            # Ensure Text gets urlencoded
            if isinstance(value, Text):
                value = quote(value)
            converted[key] = value

        # TODO: we may have to split off the query from the rest as long as the
        # query is possibly part of the path template.
        # the first stuff just gets used as-is (and if the path sucks so be it)
        # but the query stuff has to be urlencode() instead of format()
        # that's tedious to deal with
        # maybe we just need to separate path parameters from query parameters
        # from body parameters. but for now that much design is too much time

        template = self.path + ("?{}".format(self.query) if self.query else "")
        return template.format(**converted)

    def url(self, base, values):
        # type: (Text, dict[Text, Text]) -> Text
        """Generate an absolute URL for this endpoint.

        :arg url:
            Base URL to append the endpoint's relative URI to.
        :arg values:
            Dictionary of arguments.
        """
        # TODO: error message
        if not base or not base.startswith(("http://", "https://")):
            raise URLError()
        return "/".join([
            base.rstrip("/"),
            self.uri(values=values).lstrip("/"),
        ])

    def headers(self, values):
        """
        This can be overridden to specify headers as a function of passed
        parameters.
        """
        return self._headers.copy()

    def request(self, method, base, values=None, headers=None, body=None):
        # type: (Text, Text, Optional[dict[Text, Text]], Optional[Headers], Optional[bytes]) -> Request
        """Generate a description of an HTTP request.

        This method can be overridden to customize generated requests for a
        particular kind of service.

        :arg method:
        :arg base:
            Base URL
        :arg values:
            Dictionary of arguments, if any are needed
        :arg headers:
            Optional. Headers that will override any others specified.
        :arg body:
        """
        # Allow self.headers overrides to reflect here
        self_headers = self.headers(values)

        # Combine own headers with passed headers - passed get precedence
        headers = Headers.merged(self_headers, headers)

        # Allow self.url customizations on top of the passed URL
        url = self.url(base=base, values=values)

        # TODO: blegh
        method_bytes, url_bytes = [
            (text.encode("utf-8") if not isinstance(text, bytes) else text)
            for text in [method, url]
        ]

        return Request(
            method=method_bytes,
            url=url_bytes,
            headers=headers,
            body=body,
        )


class Host(object):
    """Store information associated with a specific host.

    :note: This interface is still in flux and still has some wrinkles.

    Hosts are passed to methods of Service or Endpoint so that they can convert
    relative URIs into absolute URLs.
    """
    def __init__(self, url, headers=None):
        # type: (Text, Optional[Headers]) -> None
        """
        :arg url:
            Base URL.
            This must not contain URL parameters.
        :arg headers:
            Optional. HTTP header overrides to use for the given host.
            These take precedence over anything on a service or endpoint
            definition.
        """
        self._url = url
        self._headers = headers or Headers()

    @property
    def url(self):
        # type: () -> Text
        return self._url

    def headers(self):
        # type: () -> Headers
        """Generate a dict of headers for this host.
        """
        # This method can be overridden.

        # Defensive copy.
        return self._headers.copy()


class Parameter(object):
    """One parameter, and how to validate it

    :note: this is completely TBD for now.
    """
    def __init__(self, options=None):
        # type: (Optional[Sequence[Text]]) -> None
        """
        :arg options:
            If provided, this should be a list of strings that are accepted
            as arguments for this parameter.
        """
        self.options = options
