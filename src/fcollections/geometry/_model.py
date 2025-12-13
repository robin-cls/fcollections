import dataclasses as dc
from enum import Enum

import numpy as np


@dc.dataclass
class LongitudeConvention:
    """Longitude convention."""

    lon_min: float
    """Minimal longitude in degrees."""
    lon_max: float
    """Maximal longitude in degrees."""

    def __post_init__(self):
        if self.lon_max - self.lon_min != 360:
            raise ValueError("Longitude convention must define a 360° interval")

    def __str__(self):
        return f"[{self.lon_min},{self.lon_max}["

    __repr__ = __str__

    def normalize(self, lon: np.array, inplace: bool = False) -> np.array:
        """Normalize a longitude array and keep it even if it's not monotonous.

        Parameters
        ----------
        lon: np.array
            an array of longitudes
        inplace: bool
            edit input array (True) or return a copy (False)

        Returns
        -------
            an array of longitudes converted in the current convention
        """
        if not inplace:
            lon = lon.copy()

        # This is a patch to handle maximum convention intervals
        # TODO Needs to be improved by, e.g. overloading Period object
        if np.array_equal(lon, np.array([-180, 180])):
            return np.array([self.lon_min, self.lon_max])
        if np.array_equal(lon, np.array([0, 360])):
            return np.array([self.lon_min, self.lon_max])

        is_max = lon == self.lon_max
        # In place operations
        lon -= self.lon_min
        lon %= 360
        lon += self.lon_min
        lon[is_max] = self.lon_max

        return lon

    def normalize_and_split(
        self, lon: np.array, inplace: bool = False
    ) -> list[np.array]:
        """Normalize a longitude array and split it in two parts if its not
        monotonous.

        Parameters
        ----------
        lon: np.array
            an array of longitudes
        inplace: bool
            edit input array (True) or return a copy (False)

        Returns
        -------
            an list of array of longitudes converted in the current convention
        """
        lon = self.normalize(lon, inplace)
        return _split_arr(lon, self.lon_min, self.lon_max)


def _split_arr(arr: np.ndarray, val_min: float, val_max: float) -> list[np.array]:
    """Split an array of longitude coordinates if its not monotonous.

    Add min and max bounds to each split.
    """
    indice = np.where(arr == np.min(arr))[0][0]

    if indice == 0 or indice == arr.size:
        return [arr]

    sl0 = arr[slice(0, indice)]
    if sl0[-1] != val_max:
        sl0 = np.append(arr[slice(0, indice)], val_max)

    sl1 = arr[slice(indice, arr.size)]
    if sl1[0] != val_min:
        sl1 = np.insert(arr[slice(indice, arr.size)], 0, val_min)

    return [sl0, sl1]


class StandardLongitudeConvention(Enum):
    CONV_180 = LongitudeConvention(-180, 180)
    CONV_360 = LongitudeConvention(0, 360)


def guess_longitude_convention(lon: np.array) -> StandardLongitudeConvention:
    """Guess the convention used in an array of longitudes, either (-180/180)
    or (0/360)

    Parameters
    ----------
    lon: np.array
        an array of longitudes

    Returns
    -------
        the detected StandardLongitudeConvention enum

    Raises
    ------
    ValueError
        In case the input longitudes span over multiple intervals. ex: [-170, 0,
        310] uses both [-180, 180] and [0, 360] conventions and will trigger an
        exception
    """
    lon = lon[~np.isnan(lon)]

    if np.all((lon >= 0) & (lon <= 360)):
        return StandardLongitudeConvention.CONV_360

    if np.all((lon >= -180) & (lon <= 180)):
        return StandardLongitudeConvention.CONV_180

    conventions = ", ".join([str(c.value) for c in StandardLongitudeConvention])
    msg = (
        "Impossible to guess the convention: longitudes do not follow any "
        f"known convention amongst [ {conventions} ]"
    )
    raise ValueError(msg)
