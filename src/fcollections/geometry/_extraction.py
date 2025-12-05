from __future__ import annotations

import dataclasses as dc
import heapq
import logging

import geopandas as gpd
import numba.types
import numpy as np
import pandas as pda
from shapely.geometry import Polygon
from xarray import Dataset

from ._model import LongitudeConvention

logger = logging.getLogger(__name__)


@dc.dataclass
class SwathGeometriesBuilder:

    longitude_variable: str = "longitude"
    latitude_variable: str = "latitude"

    def build(
        self,
        ds: Dataset,
        pass_number: int = 0,
        convention: LongitudeConvention = LongitudeConvention(0, 360),
        nb_points: int = 500,
    ) -> gpd.GeoDataFrame:

        return self._extract_geometry(
            ds[self.longitude_variable].values,
            ds[self.latitude_variable].values,
            pass_number,
            convention,
            nb_points,
        )

    def _monotonic(self, lon: np.ndarray):
        return np.all(np.diff(lon[:, 0]) > 0)

    def _extract_geometry(
        self,
        lon: np.ndarray,
        lat: np.ndarray,
        pass_number: int,
        convention: LongitudeConvention,
        nb_points: int,
    ) -> gpd.GeoDataFrame:

        # TODO convention is useless for now:
        # TODO normalize polygon(s) to convention before return it(them)
        new_convention = convention
        if not self._monotonic(lon):
            new_convention = LongitudeConvention(-180, 180)
            lon = new_convention.normalize(lon)

        if not self._monotonic(lon):
            raise KeyError("Lon should be monotonic now!")

        arr_lon = np.concatenate((lon[:, 0], lon[:, -1][::-1]))
        arr_lat = np.concatenate((lat[:, 0], lat[:, -1][::-1]))

        reduction = visvalingam(arr_lon, arr_lat, nb_points)
        geom = Polygon(np.stack(reduction).T)

        data_geom = gpd.GeoDataFrame(
            pda.DataFrame(
                {
                    "pass_number": [pass_number],
                    "geometry": [geom],
                }
            )
        )

        data_geom.sort_values("pass_number", inplace=True)
        data_geom.reset_index(drop=True, inplace=True)

        return data_geom


@numba.njit(cache=True)
def _tri_area2(x, y, i0, i1, i2):  # pragma: no cover
    """Double area of triangle.

    :param array x:
    :param array y:
    :param int i0: indice of first point
    :param int i1: indice of second point
    :param int i2: indice of third point
    :return: area
    :rtype: float
    """
    x0, y0 = x[i0], y[i0]
    x1, y1 = x[i1], y[i1]
    x2, y2 = x[i2], y[i2]
    p_area2 = (x0 - x2) * (y1 - y0) - (x0 - x1) * (y2 - y0)
    return abs(p_area2)


@numba.njit(cache=True)
def visvalingam(x, y, fixed_size=18):  # pragma: no cover
    """Polygon simplification with visvalingam algorithm.

    X, Y are considered like a polygon, the next point after the last
    one is the first one

    :param array x:
    :param array y:
    :param int fixed_size: array size of out
    :return: New (x, y) array, last position will be equal to first one,
        if array size is 6, there is only 5 point.
    :rtype: array,array
    """
    # TODO :  in case of original size less than fixed size, jump at the end
    nb = x.shape[0]
    nb_ori = nb
    # Get indice of first triangle
    i0, i1 = nb - 2, nb - 1
    # Init heap with first area and tiangle
    h = [(_tri_area2(x, y, i0, i1, 0), (i0, i1, 0))]
    # Roll index for next one
    i0 = i1
    i1 = 0
    # Index of previous valid point
    i_previous = np.empty(nb, dtype=numba.types.int64)
    # Index of next valid point
    i_next = np.empty(nb, dtype=numba.types.int64)
    # Mask of removed
    removed = np.zeros(nb, dtype=numba.types.bool_)
    i_previous[0] = -1
    i_next[0] = -1
    for i in range(1, nb):
        i_previous[i] = -1
        i_next[i] = -1
        # We add triangle area for all triangle
        heapq.heappush(h, (_tri_area2(x, y, i0, i1, i), (i0, i1, i)))
        i0 = i1
        i1 = i
    # we continue until we are equal to nb_pt
    while nb >= fixed_size:
        # We pop lower area
        _, (i0, i1, i2) = heapq.heappop(h)
        # We check if triangle is valid(i0 or i2 not removed)
        if removed[i0] or removed[i2]:
            # In this cas nothing to do
            continue
        # Flag obs like removed
        removed[i1] = True
        # We count point still valid
        nb -= 1
        # Modify index for the next and previous, we jump over i1
        i_previous[i2] = i0
        i_next[i0] = i2
        # We insert 2 triangles which are modified by the deleted point
        # Previous triangle
        i_1 = i_previous[i0]
        if i_1 == -1:
            i_1 = (i0 - 1) % nb_ori
        heapq.heappush(h, (_tri_area2(x, y, i_1, i0, i2), (i_1, i0, i2)))
        # Previous triangle
        i3 = i_next[i2]
        if i3 == -1:
            i3 = (i2 + 1) % nb_ori
        heapq.heappush(h, (_tri_area2(x, y, i0, i2, i3), (i0, i2, i3)))
    x_new, y_new = np.empty(fixed_size, dtype=x.dtype), np.empty(
        fixed_size, dtype=y.dtype
    )
    j = 0
    for i, flag in enumerate(removed):
        if not flag:
            x_new[j] = x[i]
            y_new[j] = y[i]
            j += 1
    # we copy first value to fill array end
    x_new[j:] = x_new[0]
    y_new[j:] = y_new[0]
    return x_new, y_new
