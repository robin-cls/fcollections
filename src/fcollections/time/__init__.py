"""Time conversion utilities, Period definition and operations."""

from __future__ import annotations

import dataclasses as dc
import typing as tp

import numpy as np

from ._conversions import (
    CNES_DATE_REFERENCE,
    MILLENNIUM_DATE_REFERENCE,
    fractional_julian_day_to_numpy,
    julian_day_to_numpy,
    numpy_to_fractional_julian_day,
    numpy_to_julian_day,
)
from ._operations import (
    fuse_successive_periods,
    periods_envelop,
    periods_holes,
)
from ._periods import Period

if tp.TYPE_CHECKING:  # pragma: no cover
    import numpy.typing as np_t

__all__ = [
    "Period",
    "fuse_successive_periods",
    "periods_envelop",
    "periods_holes",
    "numpy_to_fractional_julian_day",
    "numpy_to_julian_day",
    "julian_day_to_numpy",
    "fractional_julian_day_to_numpy",
    "CNES_DATE_REFERENCE",
    "MILLENNIUM_DATE_REFERENCE",
    "times_holes",
    "ISODuration",
]


def times_holes(
    times: np_t.NDArray[np.datetime64], sampling: np.timedelta64
) -> tp.Generator[Period, None, None]:
    delta_t = np.diff(times)
    yield from map(
        lambda ii: Period(
            times[ii], times[ii + 1], include_start=False, include_stop=False
        ),
        np.where(delta_t > 1.5 * sampling.astype("m8[ns]"))[0],
    )


@dc.dataclass(eq=True, frozen=True)
class ISODuration:
    """ISO8601 duration.

    We must redefine as class different from numpy.timedelta64 or
    datetime64 because years and months can be coded in ISO duration.
    """

    years: int = 0
    """Years."""
    months: int = 0
    """Months."""
    weeks: int = 0
    """Weeks."""
    days: int = 0
    """Days."""
    hours: int = 0
    """Hours."""
    minutes: int = 0
    """Minutes."""
    seconds: float = 0.0
    """Seconds."""
