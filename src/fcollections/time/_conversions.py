import numpy as np

CNES_DATE_REFERENCE = np.datetime64("1950-01-01")
MILLENNIUM_DATE_REFERENCE = np.datetime64("2001-01-01T00:00:00")


def julian_day_to_numpy(
    julian_day: tuple[int, int, float], reference: np.datetime64 = CNES_DATE_REFERENCE
) -> np.datetime64:
    """Converts a julian (day, hour, seconds) to a numpy datetime.

    Parameters
    ----------
    julian_day
        Julian day given as a tuple (day, hour, seconds), where seconds can be a
        floating point number
    reference
        Reference for the julian days (defaults to 1950-01-01)

    Returns
    -------
    timestamp
        Numpy datetime64 matching the julian day, with a microseconds precision
    """
    return (
        reference
        + np.timedelta64(julian_day[0], "D")
        + np.timedelta64(julian_day[1], "h")
        + np.timedelta64(int(np.round(julian_day[2] * 1e6)), "us")
    )


def fractional_julian_day_to_numpy(
    fractional_day: float, reference: np.datetime64 = CNES_DATE_REFERENCE
) -> np.datetime64:
    """Converts a fractional julian day to a numpy datetime.

    Parameters
    ----------
    julian_day
        Julian day given as a floating point number. The integral part is
        directly interpreted as the number of days since the reference. The
        fractional part must be converted to hour, minutes and seconds before
        building the numpy timestamp
    reference
        Reference for the julian days (defaults to 1950-01-01)

    Returns
    -------
    timestamp
        Numpy datetime64 matching the fractional julian day, with a microseconds
        precision
    """
    day_fraction, day = np.modf(fractional_day)
    hour_fraction, hour = np.modf(day_fraction * 24)
    return julian_day_to_numpy(
        (int(day), int(hour), hour_fraction * 3600), reference=reference
    )


def numpy_to_julian_day(
    timestamp: np.datetime64, reference: np.datetime64 = CNES_DATE_REFERENCE
) -> tuple[int, int, float]:
    """Converts a numpy datetime to julian day as a tuple (day, hour, seconds).

    Parameters
    ----------
    timestamp
        timestamp given as a numpy datetime
    reference
        Reference for the julian days (defaults to 1950-01-01)

    Returns
    -------
    julian_day
        Julian day given as a tuple (day, hour, seconds), where seconds can be a
        floating point number
    """
    delta = timestamp - reference
    days = delta // np.timedelta64(1, "D")
    hours = (delta - np.timedelta64(days, "D")) // np.timedelta64(1, "h")
    seconds = (
        delta - np.timedelta64(days, "D") - np.timedelta64(hours, "h")
    ) / np.timedelta64(1, "s")
    return days, hours, seconds


def numpy_to_fractional_julian_day(
    timestamp: np.datetime64, reference: np.datetime64 = CNES_DATE_REFERENCE
) -> float:
    """Converts a numpy datetime to fractional julian day.

    Parameters
    ----------
    timestamp
        timestamp given as a numpy datetime
    reference
        Reference for the julian days (defaults to 1950-01-01)

    Returns
    -------
    julian_day
        Julian day given as a floating point number. The integral part is
        directly interpreted as the number of days since the reference. The
        fractional part is the combination of the hours, minutes and seconds
        from the numpy timestamp. The fractional part has a microsecond
        precision
    """
    delta = timestamp - reference
    return delta / np.timedelta64(1, "D")
