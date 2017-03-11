"""This module is a place for code which customizes a BCS service definition.
"""

from decimal import Decimal
from typing import Text
from because.services.headers import DEFAULT_HEADERS
from because.service import Service, Endpoint
from . parse import parse


WRAPPED_SERVICES = set([
    "mapbox",
    "mapzen",
    # "graphhopper",
])


class RoutingService(Service):
    """Define endpoints for BCS routing service.
    """
    def __init__(self):
        # type: () -> None
        endpoints = {

            # Trailing slash needed if no auth
            # Refers to wrapped versions of services
            u"metadata": Endpoint(
                path="/routings/",
            ),
            
            u"latlon": Endpoint(
                path=(
                    "/route/{service}"
                    "/originx/{origin_x}"
                    "/originy/{origin_y}"
                    "/destinationx/{destination_x}"
                    "/destinationy/{destination_y}"
                ),
                parameters={
                    "service": WRAPPED_SERVICES,
                    # not yet sure if Decimal is the right way
                    "origin_x": Decimal,
                    "origin_y": Decimal,
                    "destination_x": Decimal,
                    "destination_y": Decimal,
                }
            ),

            u"address": Endpoint(
                path=(
                    "/route/{service}"
                    "/originaddress/{origin}"
                    "/destinationaddress/{destination}"
                ),
                parameters={
                    "service": WRAPPED_SERVICES,
                    "origin": Text,
                    "destination": Text,
                }
            ),

            # give origin/destination addresses, get route
            u"waypoints": Endpoint(
                # TODO: ensure urlencoding for the pipes, not just as one off
                # TODO: how to encode unlimited waypoints?
                # can map "addresses" to Sequence[Text], but have to also
                # specify how that is serialized into a URL, kind of gross
                path="/route/{service}/",
                query="waypoints={waypoints}",
                parameters={
                    "service": WRAPPED_SERVICES,
                    "waypoints": Text,
                },
            ),

            # Coming soon
            u"batch": Endpoint(
                path="/route/{service}/batch",
                parameters={
                },
            ),

            u"batch_status": Endpoint(
                path="/route/{service}/batch/{uuid}",
                parameters={
                    "uuid": Text,
                },
            ),
        }
        super(RoutingService, self).__init__(
            endpoints,
            headers=DEFAULT_HEADERS,
        )

    def parse(self, response):
        return parse(response)
