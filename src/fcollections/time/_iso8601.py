import dataclasses as dc
import re


@dc.dataclass
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

    def __str__(self) -> str:
        """Convert ISODuration to ISO8601 code.

        ISO codes looks like PT1S, P1W, ...

        Returns
        -------
        :
            ISO8601 code
        """
        if not any(vars(self).values()):
            return "PT0S"

        date_parts = []
        time_parts = []

        if self.years:
            date_parts.append(f"{self.years}Y")
        if self.months:
            date_parts.append(f"{self.months}M")
        if self.weeks:
            date_parts.append(f"{self.weeks}W")
        if self.days:
            date_parts.append(f"{self.days}D")

        if self.hours:
            time_parts.append(f"{self.hours}H")
        if self.minutes:
            time_parts.append(f"{self.minutes}M")
        if self.seconds:
            # Supprime les .0 inutiles
            sec = int(self.seconds) if self.seconds.is_integer() else self.seconds
            time_parts.append(f"{sec}S")

        if time_parts:
            return "P" + "".join(date_parts) + "T" + "".join(time_parts)

        return "P" + "".join(date_parts)


_ISO_8601_DURATION = re.compile(
    r"""
    ^P
    (?:(?P<years>\d+)Y)?
    (?:(?P<months>\d+)M)?
    (?:(?P<weeks>\d+)W)?
    (?:(?P<days>\d+)D)?
    (?:T
        (?:(?P<hours>\d+)H)?
        (?:(?P<minutes>\d+)M)?
        (?:(?P<seconds>\d+(?:\.\d+)?)S)?
    )?
    $
    """,
    re.VERBOSE,
)


def parse_iso8601_duration(value: str) -> ISODuration:
    """Parse ISO 8601 duration (P1D, PT3H, P1DT15M, ...)

    Parameters
    ----------
    value
        The ISO8601 code to parse

    Returns
    -------
    :
        The ISODuration object

    Raises
    ------
    ValueError
        In case the input does not match a valid ISO8601 duration code
    """
    match = _ISO_8601_DURATION.match(value)
    if not match:
        msg = f"Invalid ISO 8601 duration : {value}"
        raise ValueError(msg)

    parts = {
        name: (
            int(val)
            if val and name != "seconds"
            else float(val) if name == "seconds" and val else 0
        )
        for name, val in match.groupdict().items()
    }

    return ISODuration(**parts)
