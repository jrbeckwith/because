"""
Combine boundless service definitions with host definitions to provide a
very high-level, all-in-one interface for quickstarts.
"""

from logging import Logger, getLogger as get_logger
from typing import (
    Any,
    Optional,
)
from . errors import InvalidObject
from . response import Response
from . ssl_config import SSLConfig
from . headers import Headers
from . future import Result, Present
from . services.token.service import TokenService
from . services.search.service import SearchService
from . services.routing.service import RoutingService
from . services.basemaps.service import BasemapsService
from . services.geocoding.service import GeocodingService
from . hosts import HOSTS
from . interfaces import INTERFACES


LOG = get_logger(__name__)


class NotLoggedIn(Exception):
    """Raised when non-token requests are made without logging in first.
    """
    def __init__(self):
        super(NotLoggedIn, self).__init__(
            "run login() and let it finish before running other methods"
        )


# It won't work to directly provide a Client subclass because then we can't use
# arbitrary Client implementations.
# We also can't require users to construct their own Client.
# Therefore, we have to create a Client.
# So we have to know which flavor to use.

class Frontend(object):
    """
    """
    log = LOG.getChild("Frontend")

    def __init__(
            self,
            interface="python",
            env="dev",
            ssl_config=None,
            log=None,
    ):
        # type: (str, str, Optional[SSLConfig], Optional[Logger]) -> None
        """
        """

        client_cls = INTERFACES.get(interface)
        if client_cls is None:
            raise InvalidObject("no known interface {0!r}".format(interface))

        self.host = HOSTS.get(env)
        if not self.host:
            raise InvalidObject("no known host for env {0!r}".format(env))

        self.client = client_cls(
            ssl_config=ssl_config,
            log=log,
        )

        self.log = log or self.log

        # Instantiate all the services on top of our base URL

        self.token_service = TokenService()
        self.routing_service = RoutingService()
        self.geocoding_service = GeocodingService()
        self.basemaps_service = BasemapsService()
        self.search_service = SearchService()

        # Store token to use in Authorization headers
        self.token = None  # type: Optional[bytes]

        # Cache basemaps from the enumeration endpoint.
        # Indexed by strings like "Mapbox Satellite"
        self._basemaps = None  # type: Any

    def headers(self):
        if not self.token:
            raise NotLoggedIn()
        return Headers([
            (
                b"Authorization", "Bearer {0}".format(
                    self.token.as_text(),
                ).encode("utf-8")
            ),
        ])

    def login(self, username, password):
        # type: (bytes, bytes) -> Result
        """Use the token service to grab an auth token.

        This should be run before other methods.
        """
        # TODO: consider returning cached token if already exists.
        # Then login can be put at the head of future chains for each service.

        request = self.token_service.login_request(
            self.host.url, username, password,
        )
        self.log.debug("login request: %r", request)

        def cache_login(response):
            # self is closed over from the outer scope, therefore retained
            # wherever this callback ends up.
            token = self.token_service.parse(response)
            self.token = token
            return token

        # Methods like frontend.login() need to sequence work after results
        # are received. Normally we'd ensure this by just blocking, but
        # async implementations like Qt reasonably expect not to block.
        # However, there is no specific async interface we can take for granted
        # on Python 2, and even in Python 3 we still have Qt vs. asyncio vs.
        # curio or whatever.
        # So what we do is abstract over these...
        #
        # Here, in this method, we have to return something right away and cede
        # control. But control doesn't need to come back to this method if it
        # goes to something which does what we need it to - a callback,
        # in this case cache_login. Callbacks will work everywhere. But,
        # instead of messily passing a callback to client.send, we can wrap the
        # transfer in a Result: when the result is waited on by whatever
        # mechanism, it waits on the transfer, then the resulting response is
        # passed to the callback, and the result yields up whatever the
        # callback returned.
        transfer = self.client.send(request)
        return Result(transfer, cache_login)

    def basemaps(self):
        """Use the basemaps service to enumerate available basemaps.

        For now this has to be called and waited on before doing basemap
        stuff... :(
        """
        if not self.token:
            raise NotLoggedIn()

        # Return from cache
        if self._basemaps:
            return Present(self._basemaps)

        request = self.basemaps_service.request(
            u"metadata",
            method=u"GET",
            base=self.host.url,
            headers=self.headers(),
        )

        # Ask client to start sending the request.
        # It gives us a transfer, which is a "future" - an IOU for the eventual
        # result.
        transfer = self.client.send(request)
        # Now the request is running "in the background."

        # Now we're going to define a function that will be called when the
        # transfer is complete, yielding a response. This function takes the
        # response, parses it, *caches the result* and then returns the result.
        def cache_basemaps(response):
            """Define how to intercept basemaps requests to cache results.
            """
            basemaps = self.basemaps_service.parse_metadata(response)
            self._basemaps = basemaps
            return basemaps

        # Now we wrap the transfer in a result: when the caller waits on this
        # result, the result waits on the transfer, then runs cache_basemaps to
        # cache the result on this Frontend instance, then return the result.
        return Result(transfer, cache_basemaps)

    def basemap(self, name):
        """Get the basemap of the specified name.

        If there is no such basemap, returns None.
        """
        if not self.token:
            raise NotLoggedIn()

        # To be run on the result of self.basemaps().
        def extract_basemap(basemaps):
            return basemaps.get(name.lower())

        return Result(self.basemaps(), extract_basemap)

    def geocode(self, address, service="mapbox"):
        """Use the geocoding service to geocode an address.
        """
        if not self.token:
            raise NotLoggedIn()

        if not address:
            raise Exception("FIXME")

        request = self.geocoding_service.request(
            u"forward",
            method=u"GET",
            base=self.host.url,
            values={
                "service": service,
                "address": address,
            },
            headers=self.headers(),
        )
        transfer = self.client.send(request)
        return Result(transfer, self.geocoding_service.parse_forward)

    def reverse_geocode(self, x, y, service="mapbox"):
        """Use the geocoding service to reverse-geocode a location.
        """
        if not self.token:
            raise NotLoggedIn()

        request = self.geocoding_service.request(
            u"reverse",
            method=u"GET",
            base=self.host.url,
            values={
                "service": service,
                "x": x,
                "y": y,
            },
            headers=self.headers(),
        )
        transfer = self.client.send(request)
        return Result(transfer, self.geocoding_service.parse_reverse)

    def route(self, origin, *waypoints, **kwargs):
        """Use the routing service to get a route through locations/addresses.
        """
        # These wouldn't be in **kwargs but Python 2 is lacking
        service = kwargs.get("service") or "mapbox"

        if not self.token:
            raise NotLoggedIn()

        if not origin or not waypoints:
            raise Exception("FIXME")
        waypoints = "|".join([origin] + list(waypoints))

        request = self.routing_service.request(
            u"waypoints",
            method=u"GET",
            base=self.host.url,
            values={
                "service": service,
                "waypoints": waypoints,
            },
            headers=self.headers(),
        )
        transfer = self.client.send(request)
        return Result(transfer, self.routing_service.parse)

    def search_categories(self):
        if not self.token:
            raise NotLoggedIn()

        request = self.search_service.request(
            u"categories",
            method=u"GET",
            base=self.host.url,
            values={
            },
            headers=self.headers(),
        )
        transfer = self.client.send(request)
        return Result(transfer, self.search_service.parse_categories)

    def search_category(self, category, q):
        if not self.token:
            raise NotLoggedIn()

        request = self.search_service.request(
            u"category",
            method=u"GET",
            base=self.host.url,
            values={
                "category": category,
                "q": q,
            },
            headers=self.headers(),
        )
        transfer = self.client.send(request)
        return Result(transfer, self.search_service.parse_category)

    def opensearch(self, query, category="ALL", start_page=0, page_size=20):
        if not self.token:
            raise NotLoggedIn()

        request = self.search_service.request(
            u"opensearch",

            method=u"GET",
            base=self.host.url,
            values={
                # search terms
                "q": query,
                # starting page, default 0
                "si": start_page,
                # number of records per page, default 20
                "c": page_size,
                # search category, LC or DOC
                "cat": category,
            },
            headers=self.headers(),
        )
        transfer = self.client.send(request)
        return Result(transfer, self.search_service.parse_opensearch)

    def search_data(self):
        if not self.token:
            raise NotLoggedIn()

        # TODO: to use this, need to figure out the syntax of the POST body

        request = self.search_service.request(
            # This tells us that GET isn't allowed, 405
            # what should I use then?
            u"data",
            method=u"POST",
            base=self.host.url,
            values={
                # ???
            },
            headers=self.headers(),
        )
        transfer = self.client.send(request)
        return Result(transfer, self.search_service.parse_data)

    def search_osd(self):
        if not self.token:
            raise NotLoggedIn()

        request = self.search_service.request(
            # This makes a cool stack trace
            u"opensearchdescription.xml",
            method=u"GET",
            base=self.host.url,
            values={
            },
            headers=self.headers(),
        )
        transfer = self.client.send(request)
        return Result(transfer, self.search_service.parse_osd)
