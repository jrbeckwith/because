"""This module is a place for code which customizes a BCS service definition.
"""

import json
from typing import Text
from because.errors import ParseError
from because.services.headers import DEFAULT_HEADERS
from because.headers import Headers
from because.service import Service, Endpoint
from . search_category import SearchCategory
from . search_result import SearchResult, parse_opensearch_xml
# TODO Should be standard repr
# from . goemetry import Geometry


class SearchService(Service):
    """Define endpoints for BCS search service.
    """
    def __init__(self):
        # type: () -> None
        endpoints = {
            # bcs/bcs-search-service/src/main/java/com/boundlessgeo/bcs/services/OpenSearchService.java

            # Gives a nice traceback, we have that going for us
            u"opensearchdescription.xml": Endpoint(
                "/search/opensearchdescription.xml",
                parameters={},
            ),

            # XML interface to the same old stuff
            u"opensearch": Endpoint(
                "/search/open",
                query="q={q}&si={si}&c={c}&cat={cat}",
                parameters={
                    "q": Text,
                    "si": int,
                    "c": int,
                    "cat": Text,
                },
                headers=Headers([
                    # We don't want JSON, so don't ask for it
                    (b"Accept", b"application/atom+xml"),
                ]),
            ),

            # DataSearchService:
            # bcs/bcs-search-service/src/main/java/com/boundlessgeo/bcs/services/DataSearchService.java
            #
            # SpatialDataQuery:
            # bcs/bcs-search-service/src/main/java/com/boundlessgeo/bcs/data/SpatialDataQuery.java
            # contains (methods generated by @Data):
            # SpatialTemporalSearchBroker:
            # bcs/bcs-search-service/src/main/java/com/boundlessgeo/bcs/brokers/SpatialTemporalSearchBroker.java
            # contains:
            # GeoJsonResult search(Polygon poly, DateTime start, DateTime stop, int startIndex, int count);
            # apparently only implemented by PlanetImageryBroker:
            # bcs/bcs-search-service/src/main/java/com/boundlessgeo/bcs/brokers/PlanetImageryBroker.java
            u"data": Endpoint(
                "/search/data/",
                parameters={},
            ),

            u"categories": Endpoint(
                "/search/categories",
                parameters={},
            ),

            u"category": Endpoint(
                "/search/categories/{category}",
                query="q={q}",
                parameters={
                    "category": Text,
                    "q": Text,
                },
            ),
        }
        super(SearchService, self).__init__(
            endpoints,
            headers=DEFAULT_HEADERS,
        )

    def parse_data(self, response):
        return response

    def parse_osd(self, response):
        return response

    def parse_opensearch(self, response):
        if not response:
            raise ParseError("falsy response", response=response)
        if not response.body:
            raise ParseError("empty response body", response=response)
        if response.status != 200:
            raise ParseError("error response", response=response)

        content_types = response.headers[b"content-type"]
        content_type = content_types[0] if content_types else None
        if not content_type:
            raise ParseError(
                "no content-type in response headers",
                response=response,
            )
        elif not content_type.startswith(b"application/atom+xml"):
            raise ParseError(
                "unexpected content-type {0!r}".format(content_type),
                response=response
            )
        return parse_opensearch_xml(response.body)

    def parse_categories(self, response):
        # TODO more checking
        records = json.loads(response.body.decode("utf-8"))

        table = {
            record["key"]: SearchCategory(
                key=record["key"],
                description=record["description"],
                service=self,
            )
            for record in records
        }

        return table

    def parse_category(self, response):
        top = json.loads(response.body.decode("utf-8"))

        # expect top["type"] == "FeatureCollection"
        features = top["features"]
        results = []
        for feature in features:
            # Ignored for now, later could be encapsulated and offered up
            # maybe set it to None if it's some stupid null island point
            # feature_type = feature["type"]
            # geometry = feature["geometry"]

            properties = feature["properties"]
            del properties["id"]
            results.append(SearchResult(**properties))

        return results