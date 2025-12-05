"""Simplified operations over Period objects.

These methods may be replaced by more generic operation over intervals
(unions, intersections and complements.
"""

from functools import reduce
from typing import Generator, Iterable, List

from ._periods import Period


def fuse_successive_periods(periods: List[Period]) -> Iterable[Period]:
    """Fuse multiple successive periods.

    It is expected that the periods are already sorted and do not overlap. The
    main use case is to have a succession of daily periods that we need to fuse
    [1st may, 2nd may[ | [2nd may, 3rd may[ -> [1st may, 3rd may[

    Parameters
    ----------
    periods
        List of periods to fuse

    Returns
    -------
        Iterable of fused periods
    """
    reduced = periods[:1]
    for period in periods[1:]:
        if reduced[-1].stop == period.start:
            reduced[-1] = Period(
                reduced[-1].start,
                period.stop,
                reduced[-1].include_start,
                period.include_stop,
            )
        else:
            reduced.append(period)

    return reduced


def periods_envelop(periods: Iterable[Period]) -> Period:
    """Envelop of a list of periods.

    Parameters
    ----------
    periods
        List of periods for which we want the encompassing interval

    Returns
    -------
    :
        The Period envelop
    """
    return reduce(lambda p1, p2: p1.union(p2), periods)


def periods_holes(periods: List[Period]) -> Generator[Period, None, None]:
    """Give a simplified complement of the input periods.

    The input periods should not overlap, else this implementation will fail to
    return the expected complement.

    [1st may, 2nd may[, [3rd may, 4th may], [5th may, 7th may]
    -> [2nd may, 3rd may[, ]4th may, 5th may[

    Parameters
    ----------
    periods
        List of periods for which we want the holes

    Returns
    -------
    :
        A period Generator representing the holes in the periods list
    """
    for ii in range(len(periods) - 1):
        yield Period(
            start=periods[ii].stop,
            stop=periods[ii + 1].start,
            include_start=not periods[ii].include_stop,
            include_stop=not periods[ii + 1].include_start,
        )
