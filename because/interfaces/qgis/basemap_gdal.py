"""Tools for working with basemap services provided by Boundless.
"""
import textwrap

from because.point import Point
# from because.bbox import Bbox
from because.errors import InvalidObject

from qgis.core import (
    QgsRectangle,
    QgsCoordinateReferenceSystem,
    QgsRasterLayer,
)


class _BoundingBox(object):
    """Bounding box representation for internal use.

    This is to keep other classes tidier by encapsulating some grody details.
    """

    def __init__(self, x_min, y_min, x_max, y_max, y_origin):
        """
        :arg x_min:
            Minimum x value.

            x_min is copyright (c) Marvel Comics.

        :arg y_min:
            Minimum y value.

        :arg x_max:
            Maximum x value.

        :arg y_max:
            Maximum y value.

        :arg y_origin:
            Explicitly specify the origin for conversion.
        """
        # Paranoid argument checking
        if y_origin not in ("bottom", "top"):
            raise InvalidObject("invalid y_origin")
        if not all(
                isinstance(item, (int, float))
                for item in [x_min, y_min, x_max, y_max]
        ):
            raise InvalidObject(
                "invalid coordinate value {0!r}"
                .format([x_min, y_min, x_max, y_max])
            )

        # Store arguments
        # Be forgiving of callers with mixed-up coordinates
        self.x_min, self.x_max = sorted([x_min, x_max])
        # self.y_min, self.y_max = sorted([y_min, y_max])
        self.y_min, self.y_max = y_min, y_max
        self.y_origin = y_origin

    @classmethod
    def coerce(cls, obj, y_origin):
        """Try to create an instance
        """
        # TODO: do we want a copy?
        if isinstance(obj, cls):
            return obj

        # Special case for convenience of PyQGIS users.
        if isinstance(obj, QgsRectangle):
            return cls.from_QgsRectangle(obj, y_origin=y_origin)

        # Otherwise, attempt to interpret it as an iterable with arguments.
        else:
            try:
                iter(obj)
            except TypeError:
                raise InvalidObject(
                    "can't coerce from non-iterable {0!r}".format(obj)
                )

            # Unpack first to allow error to raise early from coerce().
            # Item ordering per arbitrary convention of QgsRectangle parameters
            try:
                x_min, y_min, x_max, y_max = obj
            except TypeError:
                raise InvalidObject(
                    "can't coerce {0!r}".format(
                        obj,
                    )
                )
            except ValueError:
                raise InvalidObject(
                    "can't coerce {0!r} with {1} items".format(
                        obj, len(obj),
                    )
                )
            return cls(x_min, y_min, x_max, y_max)

    @classmethod
    def from_QgsRectangle(cls, rectangle, y_origin):
        """Create an instance representing the same data as a QgsRectangle.
        """
        return cls(
            rectangle.xMinimum(), rectangle.yMinimum(),
            rectangle.xMaximum(), rectangle.yMaximum(),
            y_origin=y_origin,
        )

    @classmethod
    def to_QgsRectangle(cls, x_min, y_min, x_max, y_max):
        return QgsRectangle(x_min, y_min, x_max, y_max)

    def _upper_left(self):
        if self.y_origin == "top":
            point = Point(self.x_min, self.y_min)
        else:
            point = Point(self.x_min, self.y_max)
        return point

    upper_left = property(_upper_left)

    def _lower_right(self):
        if self.y_origin == "top":
            point = Point(self.x_max, self.y_max)
        else:
            point = Point(self.x_max, self.y_min)
        return point

    lower_right = property(_lower_right)


class _TMSConfig(object):
    """Bundle up parameters for a GDAL_WMS TMS definition.

    This holds the data needed to generate an XML blob for QgsRasterLayer.

    For details on the meanings of the parameters, see
    http://www.gdal.org/frmt_wms.html
    """

    def __init__(
            self,
            endpoint,
            projection="EPSG:3857",
            y_origin="top",
            bbox=None,
            tile_level=18,
            tile_count_x=1,
            tile_count_y=1,
            block_size_x=256,
            block_size_y=256,
            image_format="png",
            bands_count=3,
            user_agent=None,
    ):
        """
        :arg endpoint:
            Service URL template for a basemap service.

            Interpolation in the query string will cause GDAL to generate the
            wrong URLs.

        :arg projection:
            Projection for the raster.
            Use a string identifying an EPSG code, e.g. "EPSG:3857" (that's the
            default). XYZ TMS layers from e.g. Google, Bing or OSM should
            normally use EPSG 3857, so the default should normally work.

        :arg y_origin:
            Specify how coordinates are to be interpreted.
            Use "top" for an origin at the top left
            (per the computer graphics convention).
            Use "bottom" for an origin at the lower right
            (per the mathematical convention).

        :arg bbox:
            A bounding box as e.g. a list in the form [x_min, y_min, x_max,
            y_max].

            For the convenience of PyQGIS users, a QgsRectangle can be passed
            as well.

            This parameter is vital to the spatial interpretation of the
            raster; if the bounding box is wrong, displayed basemaps are likely
            to be displayed at an offset.

        :arg tile_level:
            Tile scale. For example, 5 approximately gives you the outlines of
            US states, 10 of medium-sized cities.

        :arg tile_count_x:

        :arg tile_count_y:

        :arg block_size_x:

        :arg block_size_y:

        :arg image_format:
            Use this to specify a different image format AND extension.
            GDAL may not need this to be specified, but it's done just in case.
            Boundless only uses PNG, so it's recommended to leave this at its
            default value when using Boundless basemap services.

        :arg bands_count:
             1 for grayscale, 3 for RGB, 4 for RGBA.

        :arg user_agent
            User-Agent string to present. Polite clients set this to identify
            themselves.
        """
        self.endpoint = endpoint.strip()
        self.projection = projection
        self.y_origin = y_origin
        self.bbox = bbox
        if bbox:
            self.bbox = _BoundingBox.coerce(bbox, y_origin=y_origin)
        self.tile_level = tile_level
        self.tile_count_x = tile_count_x
        self.tile_count_y = tile_count_y
        self.block_size_x = block_size_x
        self.block_size_y = block_size_y
        self.image_format = image_format.lower()
        self.bands_count = bands_count
        self.user_agent = user_agent or "Because"

    def as_xml(self):
        # String template for generating GDAL TMS blobs for QgsRasterLayer.
        # Since we really only need to generate one form, building up a DOM
        # here is overkill, and it would mean we have to drag in lxml which has
        # to compile C extensions, which makes users unhappy when it fails.
        xml_template = textwrap.dedent(
            """
            <GDAL_WMS>
              <Service name="TMS">
                <ServerUrl>{endpoint}</ServerUrl>
                <ImageFormat>image/{image_format}</ImageFormat>
              </Service>
              <DataWindow>
                <UpperLeftX>{upper_left.x}</UpperLeftX>
                <UpperLeftY>{upper_left.y}</UpperLeftY>
                <LowerRightX>{lower_right.x}</LowerRightX>
                <LowerRightY>{lower_right.y}</LowerRightY>
                <TileLevel>{tile_level}</TileLevel>
                <TileCountX>{tile_count.x}</TileCountX>
                <TileCountY>{tile_count.y}</TileCountY>
                <YOrigin>{y_origin}</YOrigin>
              </DataWindow>
              <Projection>{projection}</Projection>
              <BlockSizeX>{block_size.x}</BlockSizeX>
              <BlockSizeY>{block_size.y}</BlockSizeY>
              <BandsCount>{bands_count}</BandsCount>
              <Cache>
                <Extension>.{image_format}</Extension>
              </Cache>
              <UserAgent>{user_agent}</UserAgent>
              <ZeroBlockHttpCodes>403,404,503</ZeroBlockHttpCodes>
            </GDAL_WMS>
            """
        ).strip()
        upper_left = self.bbox.upper_left
        lower_right = self.bbox.lower_right
        return xml_template.format(
            endpoint=self.endpoint,
            image_format=self.image_format,
            upper_left=upper_left,
            lower_right=lower_right,
            tile_level=self.tile_level,
            # tile_count=Point(x=0, y=0),
            tile_count=Point(x=self.tile_count_x, y=self.tile_count_y),
            # tile_count_x=1,
            # tile_count_y=1,
            projection=self.projection,
            block_size=Point(x=self.block_size_x, y=self.block_size_y),
            # block_size=Point(x=1, y=1),
            # block_size_x=1,
            # block_size_y=1,
            bands_count=self.bands_count,
            y_origin=self.y_origin,
            user_agent=self.user_agent,
        )


class GDALBasemapLayer(QgsRasterLayer):
    """An XYZ basemap layer implemented using QgsRasterLayer, based on GDAL.

    This technique offloads the downloading details, but it isn't very
    flexible and it still requires building a complex XML blob for GDAL.
    """

    # 3857 is the conventional CRS for XYZ TMS layers.
    _crs_3857 = QgsCoordinateReferenceSystem(3857)

    # Magical bounding box. Don't ask what's inside.
    _default_bbox = _BoundingBox(
        x_min=-20037508.34,
        y_min=20037508.34,
        # y_min=-20037508.34,
        x_max=20037508.34,
        y_max=-20037508.34,
        # y_max=20037508.34,
        y_origin="top"  # guess?
    )

    def __init__(self, endpoint, name, user_agent=None, y_origin="top"):
        """
        :arg endpoint:
            Endpoint template for the basemap service to use.

        :arg name:
            Name for the layer.

        :arg user_agent:
            User-Agent string to send to the service.
            Please be polite and specify your own.
        """
        config = _TMSConfig(
            endpoint=endpoint,
            bbox=self._default_bbox,
            user_agent=user_agent,
            # Boundless basemaps should normally use these defaults
            y_origin=y_origin,
            projection="EPSG:3857",
        )
        blob = config.as_xml()
        super(GDALBasemapLayer, self).__init__(blob, name)
        self.setCrs(self._crs_3857)

        # Since we raise an exception in __init__, if you are holding an
        # instance just after creation, it must be valid.
        if not self.isValid():
            raise InvalidObject("invalid parameters")
