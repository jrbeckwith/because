"""This module is a place for code which customizes a BCS service definition.
"""

from typing import Text
from because.errors import ParseError
from because.response import parse_json
from because.services.headers import DEFAULT_HEADERS
from because.service import Service, Endpoint
from because.services.basemaps.basemap import Basemap
from . import parse


# TODO: use metadata endpoint to construct others somewhere...

class BasemapsService(Service):
    def __init__(self):
        # type: () -> None
        endpoints = {

            # enumerates available basemap endpoints
            u"metadata": Endpoint(
                path="/basemaps/",
                methods=["GET"],
            ),

            # "basemap" isn't defined here since there isn't just one form,
            # and the endpoints we do have probably should be discovered
            # from /basemaps/ and cached somewhere if performance is an issue.
            # For the record, individual basemaps look like e.g.
            # "/v1/basemaps/{source}/{type}/{x}/{y}/{z}"

            # e.g. /basemaps/boundless/osm
            u"xyz": Endpoint(
                path="/basemaps/{service}/{name}/{x}/{y}/{z}.png",
                query="apikey={apikey}",
                methods=["GET"],
                parameters={
                    "x": int,
                    "y": int,
                    "z": int,
                    "apikey": Text,
                }
            ),

            # e.g. mapbox and planet basemaps
            u"zxy": Endpoint(
                path="/basemaps/{service}/{name}/{z}/{x}/{y}.png",
                query="apikey={apikey}",
                methods=["GET"],
                parameters={
                    "x": int,
                    "y": int,
                    "z": int,
                    "apikey": Text,
                }
            ),

        }
        super(BasemapsService, self).__init__(
            endpoints,
            headers=DEFAULT_HEADERS,
        )

    def add_basemap(self, name, path, parameters):
        self.endpoints[name] = Endpoint(
            path=path,
            query="apikey={apikey}",
            methods=["GET"],
            parameters={
                "x": int,
                "y": int,
                "z": int,
            },
        )

    def parse_metadata(self, response):
        data = parse_json(response, required_keys=[])
        if not isinstance(data, list):
            raise ParseError(
                "unexpected type for JSON response body",
                response=response,
            )
        table = {}
        for record in data:
            basemap = parse.dict_to_basemap(record)
            table[basemap.title.lower()] = basemap
        return table
