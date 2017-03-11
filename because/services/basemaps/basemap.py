"""Represent results from the basemap discovery endpoint.
"""
import re

from because.pretty import PrettyMixin
from because.errors import InvalidObject


class InvalidBasemap(InvalidObject):
    """Raised when the state of a Basemap instance would be invalid.
    """


class Basemap(PrettyMixin):
    """Describes a basemap result from the basemaps discovery endpoint.
    """
    # methods: always just GET.
    def __init__(
            self, url,
            standard="XYZ",
            tile_format="PNG",
            title=None,
            attribution="Boundless",
            access_list=None,
            description="",
            thumbnail=None,
            headers=None,
            style_url=None,
    ):
        """
        :arg url:
            URI template to use. This will probably specify how to encode x, y,
            and z coordinates and any other parameters needed.
        :arg title:
            Title like "Boundless OSM Basemap" (aka 'name' in /basemaps result)
        """
        self.url = url
        self.standard = standard
        self.tile_format = tile_format
        self.title = title
        self.attribution = attribution
        self.access_list = access_list
        self.description = description
        self.thumbnail = thumbnail
        self.headers = headers
        self.style_url = style_url

        # don't delete these untless implementation supports something else
        if self.tile_format not in ("PNG", "PBF"):
            raise InvalidBasemap(
                "only tile_format=PNG basemaps are supported"
            )
        if self.standard != "XYZ":
            raise InvalidBasemap(
                "only XYZ basemaps are supported"
            )

        parameter_names = re.findall("{\-?([a-zA-Z_]+)}", url)
        expected = set(["x", "y", "z"])
        if set(parameter_names) != expected:
            raise InvalidBasemap(
                "expected parameters for x, y, and z"
            )

    def pretty_tuples(self):
        return [
            ("title", self.title),
            ("url", self.url),
            ("standard", self.standard),
            ("tile_format", self.tile_format),
            ("attribution", self.attribution),
            ("description", self.description)
        ]
        # access_list
        # thumbnail
        # style_url
        # headers
