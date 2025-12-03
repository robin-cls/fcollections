from __future__ import annotations

import abc
import typing as tp

if tp.TYPE_CHECKING:  # pragma: no cover
    import xarray as xr_t


class IAreaSelector(abc.ABC):
    """Abstract selector for subsetting data depending on a geographical area.

    Parameters
    ----------
    longitude: str
        longitude field name in data
    latitude: str
        latitude field name in data
    """

    longitude: str
    latitude: str

    def __init__(self, longitude: str = "longitude", latitude: str = "latitude"):
        self.longitude = longitude
        self.latitude = latitude

    @abc.abstractmethod
    def apply(
        self, ds: xr_t.Dataset, bbox: tuple[float, float, float, float]
    ) -> xr_t.Dataset:
        """Apply a geographical selection on a dataset.

        Parameters
        ----------
        ds: xr.Dataset
            a dataset
        bbox: tuple[float, float, float, float]
            the bounding box (lon_min, lat_min, lon_max, lat_max) used to subset data
            Longitude coordinates can be provided in [-180, 180[ or [0, 360[ convention.
            If bbox's longitude crosses the -180/180 of longitude, data around the crossing and matching the bbox will be selected.
            (e.g. longitude interval: [170, -170] -> data in [170, 180[ and [-180, -170] will be retrieved)

        Returns
        -------
            the geographical subset
        """
