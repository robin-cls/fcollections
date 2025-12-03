import pyinterp as pyi
import pyinterp.geodetic as pyi_geod
import pyinterp.geohash as pyi_geoh
from shapely import MultiPolygon, Polygon

from ._model import LongitudeConvention


def expand_box(box: pyi_geod.Box, precision: int) -> pyi_geod.Box:
    """Expand a geohash box with a given precision.

    The method looks for the geohashes of the input box's corners with a given
    precision. From these two geohashes, it computes the associated bounding
    boxes and find the bigger box that covers them both.

    Parameters
    ----------
    box: pyinterp.geodetic.Box
        the box to expand
    precision: int
        the precision to expand the box to

    Returns
    -------
        a pyinterp.geodetic.Box expanded to a lower precision
    """
    geohashes = pyi_geoh.encode(
        [box.min_corner.lon, box.max_corner.lon],
        [box.min_corner.lat, box.max_corner.lat],
        precision=precision,
    )

    min_lon, min_lat, max_lon, max_lat = (None,) * 4
    for g in geohashes:
        box = pyi.GeoHash.from_string(g).bounding_box()
        min_lon = (
            min(box.min_corner.lon, min_lon)
            if min_lon is not None
            else box.min_corner.lon
        )
        max_lon = (
            max(box.max_corner.lon, max_lon)
            if max_lon is not None
            else box.max_corner.lon
        )
        min_lat = (
            min(box.min_corner.lat, min_lat)
            if min_lat is not None
            else box.min_corner.lat
        )
        max_lat = (
            max(box.max_corner.lat, max_lat)
            if max_lat is not None
            else box.max_corner.lat
        )
    return pyi_geod.Box(
        pyi_geod.Point(min_lon, min_lat), pyi_geod.Point(max_lon, max_lat)
    )


def normalize_polygon(
    polygon: Polygon, convention: LongitudeConvention
) -> Polygon | MultiPolygon:
    """Normalize a polygon to a longitude convention. The polygon may be split
    to a MultiPolygon.

    Parameters
    ----------
    polygon: Polygon
        the polygon to normalize
    convention: LongitudeConvention
        the longitude convention to use (e.g. (-180, 180))

    Returns
    -------
        a Polygon or MultiPolygon with coordinates normalized in the new convention
    """
    # TODO This function needs to be completed and refactored
    keep_coords = []
    split_coords = []
    for x, y in polygon.exterior.coords:
        if convention.lon_min <= x and x <= convention.lon_max:
            keep_coords.append([x, y])
        if x < convention.lon_min:
            x += 360
            split_coords.append([x, y])
        if x > convention.lon_max:
            x -= 360
            split_coords.append([x, y])
    # TODO test if len(split_coords) == 0 : return keep_coords
    if len(split_coords) < 4:
        return Polygon(keep_coords)
    # TODO test if len(keep_coords) == 0 : return split_coords
    if len(keep_coords) < 4:
        return Polygon(split_coords)
    # TODO Add points of coordinates (lon_min, y) or (lon_max, y) for including boundaries, to avoid loosing data
    return MultiPolygon([Polygon(keep_coords), Polygon(split_coords)])
