import pytest
from because.service import Endpoint, Parameter
from because.services.basemaps.basemap import (
    InvalidBasemap,
    Basemap,
)
from because.services.basemaps import parse

# Standard boring valid parameters
URL = "https://example.com/herpderp/{x}/{y}/{z}"


class TestBasemap(object):

    def test_init_standard_not_xyz(self):
        with pytest.raises(InvalidBasemap):
            Basemap(url=URL, standard="NOTXYZ")

    def test_init_tile_format_not_png(self):
        with pytest.raises(InvalidBasemap):
            Basemap(url=URL, tile_format="GIF")

    def test_init_simple(self):
        # this is stupid, I know, just exercising the constructor
        basemap = Basemap(url=URL)
        assert basemap
        assert basemap.url == URL

    def test_parse(self):
        data = {
            "accessList": [
                "bcs-basemap-boundless"
            ],
            "attribution": "Boundlessgeo",
            "description": "A Boundless created OSM basemap",
            "endpoint": "http://saasy.boundlessgeo.io/basemaps/boundless/osm/{x}/{y}/{z}.png",
            "name": "Boundless OSM Basemap",
            "standard": "XYZ",
            "thumbnail": None,
            "tileFormat": "PNG"
        }
        basemap = parse.dict_to_basemap(data)
        assert basemap.access_list == ["bcs-basemap-boundless"]
        assert basemap.attribution == "Boundlessgeo"
        assert basemap.description == "A Boundless created OSM basemap"
        assert basemap.title == "Boundless OSM Basemap"
        assert basemap.standard == "XYZ"
        assert basemap.thumbnail is None
        assert basemap.tile_format == "PNG"
