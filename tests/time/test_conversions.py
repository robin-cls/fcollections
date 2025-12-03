import numpy as np
import pytest

from fcollections.time import (
    CNES_DATE_REFERENCE,
    MILLENNIUM_DATE_REFERENCE,
    fractional_julian_day_to_numpy,
    julian_day_to_numpy,
    numpy_to_fractional_julian_day,
    numpy_to_julian_day,
)


@pytest.mark.parametrize(
    "fractional_day, julian_day, timestamp, reference",
    [
        (27332, (27332, 0, 0.0), "2024-10-31", CNES_DATE_REFERENCE),
        (27332.25, (27332, 6, 0.0), "2024-10-31T06", CNES_DATE_REFERENCE),
        (
            27332.30743813372685186,
            (27332, 7, 1362.654754),
            "2024-10-31T07:22:42.654754",
            CNES_DATE_REFERENCE,
        ),
        (
            8704.30743813372685186,
            (8704, 7, 1362.654754),
            "2024-10-31T07:22:42.654754",
            MILLENNIUM_DATE_REFERENCE,
        ),
    ],
)
def test_julian_day_conversions(
    fractional_day: float,
    julian_day: tuple[int, int, float],
    timestamp: str,
    reference: np.datetime64,
):
    timestamp = np.datetime64(timestamp)
    assert julian_day_to_numpy(julian_day, reference) == timestamp
    assert numpy_to_julian_day(timestamp, reference) == julian_day
    assert fractional_julian_day_to_numpy(fractional_day, reference) == timestamp
    assert numpy_to_fractional_julian_day(timestamp, reference) == fractional_day


def test_julian_day_conversions_precision():
    """Conversion is precise to the microseconds, not nanoseconds."""
    fractional_day, julian_day, timestamp = (
        27332.3074319844535764,
        (27332, 7, 1362.123456789),
        np.datetime64("2024-10-31T07:22:42.123456789"),
    )
    assert abs(timestamp - julian_day_to_numpy(julian_day)) < np.timedelta64(500, "us")
    assert numpy_to_julian_day(timestamp) == julian_day
    assert abs(
        fractional_julian_day_to_numpy(fractional_day) - timestamp
    ) < np.timedelta64(500, "us")
    assert (
        numpy_to_fractional_julian_day(timestamp) - fractional_day
    ) < 500 * 1e-6 / 86400
