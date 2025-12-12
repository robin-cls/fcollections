import abc
import logging

import numpy as np
import xarray as xr

from fcollections.geometry import (
    StandardLongitudeConvention,
    guess_longitude_convention,
)

from ._model import IAreaSelector

logger = logging.getLogger(__name__)


class AreaSelector1D(IAreaSelector, abc.ABC):
    """Abstract Selector for subsetting data on depending on a geographical
    area, with a 1-dimensional selection."""

    def apply(
        self, ds: xr.Dataset, bbox: tuple[float, float, float, float]
    ) -> xr.Dataset:
        # The algorithm basically detects data convention and transforms the bbox to this convention.
        # Then it selects this indices of data matching the bbox, by transposing data to a monotonous longitude.
        # Finally it selects data with indices slices.
        (lon_min, lat_min, lon_max, lat_max) = bbox

        # Need a copy, _select_2d_indices_intersect_bounds may modify the array
        # in place
        lon = ds[self.longitude].values.copy()
        lat = ds[self.latitude].values

        try:
            data_convention = guess_longitude_convention(lon).value
        except ValueError:
            msg = (
                "Input longitudes does not fit in one of the known 360° "
                "intervals. Using [0, 360] (a copy of the input will be "
                "made)"
            )
            logger.info(msg)
            data_convention = StandardLongitudeConvention.CONV_360.value
            data_convention.normalize(lon, inplace=True)
        bbox_lon_norm = data_convention.normalize(np.array((lon_min, lon_max)))

        idx = _select_2d_indices_intersect_bounds(
            lon, lat, bbox_lon_norm, (lat_min, lat_max), data_convention.lon_max
        )

        ds_sel = ds.isel(**self.dims_selection(idx))

        logger.info("Size of the dataset matching the bbox: %s", dict(ds_sel.sizes))

        return ds_sel

    @abc.abstractmethod
    def dims_selection(self, idx: tuple) -> dict:
        """Build the slice dictionary needed for selecting data subset.

        Parameters
        ----------
        idx: tuple
            indices of data intersecting an area

        Returns
        -------
            the slice dictionary needed for selecting data subset
        """


class TemporalSerieAreaSelector(AreaSelector1D):
    """Selector for subsetting temporal series data depending on a geographical
    area.

    Parameters
    ----------
    longitude
        Name of the longitude variable in the dataset to preprocess
    latitude
        Name of the latitude variable in the dataset to preprocess
    dimension
        Dimension over which the selection is performed (defaults to 'time')
    """

    def __init__(
        self,
        longitude: str = "longitude",
        latitude: str = "latitude",
        dimension: str = "time",
    ):
        super().__init__(longitude, latitude)
        self.dimension = dimension

    def dims_selection(self, idx: tuple) -> dict:
        if idx[0].size == 0:
            logger.debug("No intersection between the bbox and the dataset")
            return {self.dimension: slice(0)}

        return {self.dimension: idx[0]}


class SwathAreaSelector(AreaSelector1D):
    """Selector for subsetting swath data depending on a geographical area.

    The selection is performed on num_lines dimension.
    """

    def dims_selection(self, idx: tuple) -> dict:
        (_id, _) = idx

        if _id.size == 0:
            logger.debug("No intersection between the bbox and the dataset")
            return {"num_lines": slice(0)}

        # If one pixel of the swath is in the box, take the entire line. Use set
        # to take the unique values of num_lines (they will be repeated for each
        # num_pixels in the box)
        return {"num_lines": list(set(_id))}


class AreaSelector2D(IAreaSelector):
    """Selector for subsetting 2d grid data depending on a geographical area.

    The selection is performed on latitude and longitude dimension.
    """

    def apply(
        self, ds: xr.Dataset, bbox: tuple[float, float, float, float]
    ) -> xr.Dataset:
        # The algorithm basically detects bbox convention and transforms the data to this convention.
        # Since the data longitude can now be non-monotonous (in case data was normalized from 0/360 to -180/180),
        # it detects the indice of data passing from -180 to 180, and work on each part: it selects slices of data matching the bbox in each
        # part, and concatenate the result.
        (lon_min, lat_min, lon_max, lat_max) = bbox

        bbox_convention = guess_longitude_convention(np.array((lon_min, lon_max))).value

        lon = bbox_convention.normalize(ds[self.longitude].values)

        lat = ds[self.latitude].values

        # SEARCH FOR LATITUDE INDICES
        lat_bounds = (lat_min, lat_max)
        # No circularity in latitude
        if lat_min > lat_max:
            lat_bounds = (lat_max, lat_min)

        lat_slices = _select_slices_intersect_bounds(lat, lat_bounds)

        lat_slices = [sl for sl in lat_slices if sl is not None]

        if lat_slices == []:
            logger.debug("No intersection between the bbox and the dataset.")
            return ds.isel(**{self.longitude: slice(0), self.latitude: slice(0)})
        lat_slice = lat_slices[0]

        # SEARCH FOR LONGITUDE INDICES

        # Search for index of transition in longitude passing from 180 to -180
        indx_transition = np.where(lon == np.max(lon))[0][0] + 1

        lon_slices = []
        # Search for lon_bounds in the first part of the dataset (-180/0, 180)
        lon_slice = _select_slices_intersect_bounds(
            lon[slice(0, indx_transition)], (lon_min, lon_max)
        )
        if lon_slice is not None:
            lon_slices.extend([sl for sl in lon_slice if sl is not None])

        # If the longitude is not monotonous, search for lon_bounds in the (-180, 0) part of the dataset
        lon_slice = _select_slices_intersect_bounds(
            lon[slice(indx_transition, lon.size)], (lon_min, lon_max), indx_transition
        )
        if lon_slice is not None:
            lon_slices.extend([sl for sl in lon_slice if sl is not None])

        if lon_slices == []:
            logger.debug("No intersection between the bbox and the dataset.")
            return ds.isel(**{self.longitude: slice(0), self.latitude: slice(0)})

        ds_sel = xr.concat(
            [
                ds.isel(**{self.longitude: slice_i, self.latitude: lat_slice})
                for slice_i in lon_slices
            ],
            dim=self.longitude,
        )

        logger.info("Size of the dataset matching the bbox: %s", dict(ds_sel.sizes))

        return ds_sel


def _find_indices_in_reversed(
    array: np.array, x: float, y: float
) -> tuple[float, float]:
    """Find indices of (x, y) in array[::-1]."""
    # No circularity in bounds
    if x > y:
        (x, y) = (y, x)

    start_idx = np.searchsorted(array, x, side="left")  # including x
    end_idx = np.searchsorted(array, y, side="right")  # including y
    n = len(array)
    start_rev = n - end_idx
    end_rev = n - start_idx

    return (start_rev, end_rev)


def _select_slices_intersect_bounds(
    data: np.array, bounds: tuple[float, float], ind_start: int = 0
) -> dict[slice]:
    """Return slices of data intersecting bounds.

    Several slices may be returned if there is circularity in the
    bounds.
    """
    if data.size == 0:
        return [None]

    x0, x1 = bounds

    if not np.all(data[:-1] <= data[1:]):
        # Data is descending. Can happen for latitude coord
        data = data[::-1]

        (i, j) = _find_indices_in_reversed(data, x0, x1)
        return [_create_slice(data, bounds, i, j, ind_start)]

    (i, j) = np.searchsorted(data, bounds)

    slices = []
    # If there is circularity in bounds
    if x1 < x0:
        # If bounds<data
        if (i, j) == (0, 0) or i == j:
            return [_create_slice(data, bounds, 0, data.size, ind_start)]

    # If there is circularity in indices, we split the result in two slices
    if j < i:
        jj = data.size
        # from the start of the dataset to j
        slices.append(_create_slice(data, bounds, 0, j, ind_start))
        # from i to the end of the dataset
        slices.append(_create_slice(data, bounds, i, jj, ind_start))
        return slices

    return [_create_slice(data, bounds, i, j, ind_start)]


def _create_slice(
    data: np.array, bounds: tuple[float, float], i: int, j: int, ind_start: int
) -> slice:
    """Creates a slice with indices (i, j) returned by search_sorted."""
    if j == 0 or i >= data.size:
        if data[0] not in bounds:
            return None
        return slice(0 + ind_start, 1 + ind_start)

    if data[j % data.size] not in bounds:
        j -= 1

    return slice(
        i + ind_start, j + ind_start + 1 if j <= data.size - 1 else j + ind_start
    )


def _select_2d_indices_intersect_bounds(
    x: np.array,
    y: np.array,
    x_bounds: tuple[float, float],
    y_bounds: tuple[float, float],
    x_max: int = 180,
):
    """Returns indices of 2-dimensional data intersecting bounds."""
    x0, x1 = x_bounds
    y0, y1 = y_bounds

    # No circularity in y axis
    if y0 > y1:
        msg = (
            "Check bbox validity: y_bounds[0]={y0} > y_bounds[1]={y1} ("
            "invalid condition for latitudes)"
        )
        raise ValueError(msg)

    # Handle circularity in x axis
    if x0 > x1:
        x[x < x0] += x_max
        x1 += x_max

    idx = np.where((x >= x0) & (x <= x1) & (y >= y0) & (y <= y1))
    return idx
