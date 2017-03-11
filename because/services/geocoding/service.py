"""This module is a place for code which customizes a BCS service definition.
"""

from typing import Text
from decimal import Decimal
from because.errors import ParseError
from because.response import parse_json
from because.services.headers import DEFAULT_HEADERS
from because.service import Service, Endpoint
from . candidate import Candidate
from . import parse


WRAPPED_SERVICES = set([
    "mapbox",
    "mapzen",
])


class GeocodingService(Service):
    """Define endpoints for BCS geocoding service.
    """

    def __init__(self):
        # type: () -> None
        endpoints = {

            # Give address, get candidate lat/lons
            u"forward": Endpoint(
                path="/geocode/{service}/address/{address}",
                parameters={
                    "service": WRAPPED_SERVICES,
                    "address": Text,
                }
            ),

            # Give WGS84 lat/lon, get address
            u"reverse": Endpoint(
                path="/geocode/{service}/address/x/{x}/y/{y}",
                parameters={
                    "service": WRAPPED_SERVICES,
                    "x": (Decimal, float),
                    "y": (Decimal, float),
                },
            ),

            # Coming soon
            u"batch": Endpoint(
                path="/geocode/{service}/batch",
                parameters={
                },
            ),

        }
        super(GeocodingService, self).__init__(
            endpoints,
            headers=DEFAULT_HEADERS,
        )

    def parse_forward(self, response):
        try:
            results = parse.parse_forward_geocodes(response)
        except ParseError:
            print(response.pretty_text())
            results = []
        return results

    def parse_reverse(self, response):
        try:
            results = parse.parse_reverse_geocodes(response)
        except ParseError:
            print(response.pretty_text())
            results = []
        return results
