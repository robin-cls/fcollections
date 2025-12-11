import logging

import geopandas as gpd
import numpy as np
import shapely as shp

from fcollections.missions import MissionsPhases, Phase
from fcollections.sad import KarinFootprints

from ._model import StandardLongitudeConvention, guess_longitude_convention

logger = logging.getLogger(__name__)


def _read_geometries_file(phase: Phase) -> gpd.GeoDataFrame:
    karin_2kms_geometries_file = KarinFootprints()[phase.short_name]
    return gpd.read_file(karin_2kms_geometries_file)


def query_geometries(
    half_orbit_numbers: int | list[int],
    phase: Phase | str = MissionsPhases.science.value,
) -> gpd.GeoDataFrame:
    """Query the geometries of the given half orbits.

    Parameters
    ----------
    half_orbit_numbers: integer or list
        requested half orbit number(s)
    phase: str
        requested phase ('science', 'calval'). Default: 'science'

    Raises
    ------
    KeyError
        In case none of the requested half orbit numbers exist.

    Returns
    -------
     gpd.GeoDataFrame:
        A Geopandas dataframe containing half orbits number and geometry as Polygon
    """
    if isinstance(half_orbit_numbers, int):
        half_orbit_numbers = [half_orbit_numbers]
    if isinstance(phase, str):
        phase = MissionsPhases[phase].value

    swath_geometries = _read_geometries_file(phase)

    selection = swath_geometries.loc[
        swath_geometries.pass_number.isin(half_orbit_numbers)
    ]

    if selection.empty:
        raise KeyError(
            f"None of the requested half orbit numbers: {half_orbit_numbers} exist"
        )

    return selection


def query_half_orbits_intersect(
    bbox: tuple[float, float, float, float],
    phase: Phase | str = MissionsPhases.science.value,
) -> gpd.GeoDataFrame:
    """Query half orbits that intersect the bbox.

    Parameters
    ----------
    bbox: tuple[float, float, float, float]
        the tuple (lon_min, lat_min, lon_max, lat_max) representing the bounding box for geographical selection
        Longitude coordinates can be provided in [-180, 180[ or [0, 360[ convention.
        If bbox's longitude crosses the -180/180 of longitude, half orbits around the crossing and matching the bbox will be selected.
        (e.g. longitude interval: [170, -170] -> half orbits in [170, 180[ and [-180, -170] will be retrieved)
    phase: str
        requested phase ('science', 'calval'). Default: 'science'

    Returns
    -------
     gpd.GeoDataFrame:
        A Geopandas dataframe containing intersecting half orbits numbers and geometries
    """
    if isinstance(phase, str):
        phase = MissionsPhases[phase].value

    swath_geometries = _read_geometries_file(phase)

    (lon_min, lat_min, lon_max, lat_max) = bbox

    # Detect convention error in bbox's longitude
    lon_range = np.array((lon_min, lon_max))
    guess_longitude_convention(lon_range)

    # Create a dict with input bbox normalized in both standard conventions
    bbox_conv_dict = {
        conv: [
            (x_min, lat_min, x_max, lat_max)
            for (x_min, x_max) in conv.value.normalize_and_split(lon_range)
        ]
        for conv in StandardLongitudeConvention
    }

    select = swath_geometries.apply(_filter_intersect, bbox_conv=bbox_conv_dict, axis=1)

    return swath_geometries[select]


def _filter_intersect(row, bbox_conv):
    # Get half orbit's convention
    pass_coords = list(row.geometry.exterior.coords)
    convention = guess_longitude_convention(
        np.array([lon for (lon, lat) in pass_coords])
    )

    # Get the bbox converted to this convention
    bbox_splits = bbox_conv[convention]

    half_orbit_polygon = shp.Polygon(pass_coords)
    # Compute intersection between pass geometry and the bbox
    # bbox longitude range may have been splitted
    return np.any(
        [half_orbit_polygon.intersects(shp.geometry.box(*bbox)) for bbox in bbox_splits]
    )
