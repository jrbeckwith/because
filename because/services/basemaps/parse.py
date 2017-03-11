from . basemap import Basemap


def dict_to_basemap(data):
    """Convert from dict representing JSON object from basemap discovery
    """
    attr_mapping = {
        "accessList": "access_list",
        "attribution": "attribution",
        "description": "description",
        "endpoint": "url",
        # reserve "name" for the parameter given after service, e.g.
        # /basemaps/boundless/{osm} or /basemaps/mapbox/{outdoors}
        "name": "title",
        "standard": "standard",
        "thumbnail": "thumbnail",
        "tileFormat": "tile_format",
        "styleUrl": "style_url",
    }
    remapped = {
        attr_mapping.get(source_attr, source_attr): data[source_attr]
        for source_attr in data.keys()
    }
    return Basemap(**remapped)
