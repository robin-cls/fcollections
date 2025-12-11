import dataclasses as dc
import datetime as dt
import functools
from copy import deepcopy
from enum import Enum, auto

import numpy as np

from fcollections.time import Period


@dc.dataclass
class Phase:
    """Mission phase properties.

    These include the start and end if available. Both half orbit number and
    time are given to allow a search using these two useful information.

    Notes
    -----
    For an going phase, make sure to use a constant bound for the period even
    if it is undefined to prevent deserialization problems with dask. If we
    use datetime('now') when working on distributed workers, the module will
    be loaded with a difference OrbitPhase value for the SCIENCE enum field
    Further dask checks will spot this discrepancy of enum definition between
    different processes and will raise an error.
    """

    short_name: str
    """Acronym for describing the mission phase.

    It is usually built so that
    both mission and phase can be recognized from this short name: ex. Jason-1
    New orbit -> 'j1n'.
    """
    half_orbits: tuple[tuple[int, int], tuple[int, int] | None]
    """First and last half orbit numbers of the phase."""
    period: Period
    """First and last dates of the phase.

    For an ongoing phase, the last date is set to dt.datetime.max.
    """
    half_orbits_per_cycle: int | None = None
    """Number of half orbits in a cycle if the phase is repetitive.

    Set to none.
    """

    @property
    def cycles(self) -> tuple[int, int | None]:
        return (
            self.half_orbits[0][0],
            self.half_orbits[1][0] if self.half_orbits[1] is not None else None,
        )

    @property
    def on_going(self) -> bool:
        return self.half_orbits[1] is None or self.period.stop > np.datetime64(
            dt.datetime.now()
        )


class Missions(Enum):
    Altika = auto()
    Cfosat = auto()
    Cryosat2 = auto()
    Envisat = auto()
    Ers1 = auto()
    Ers2 = auto()
    GeosatFollowOn = auto()
    Haiyang2A = auto()
    Haiyang2B = auto()
    Haiyang2C = auto()
    Jason1 = auto()
    Jason2 = auto()
    Jason3 = auto()
    Sentinel3A = auto()
    Sentinel3B = auto()
    Sentinel6A = auto()
    Swot = auto()
    TopexPoseidon = auto()


PHASES = {
    Missions.Swot: [
        Phase(
            "calval",
            ((402, 4), (578, 4)),
            Period(
                np.datetime64("2023-01-16"),
                np.datetime64("2023-07-10"),
                include_stop=False,
            ),
            28,
        ),
        Phase(
            "science",
            ((1, 5), (399, 584)),
            Period(np.datetime64("2023-07-21"), np.datetime64(dt.datetime.max)),
            584,
        ),
    ],
    Missions.Altika: [
        Phase(
            "al",
            ((1, 1), (22, 337)),
            Period(
                np.datetime64("2013-03-14"),
                np.datetime64("2015-04-01"),
                include_stop=False,
            ),
        ),
        Phase(
            "alg",
            ((22, 338), None),
            Period(np.datetime64("2015-03-31"), np.datetime64(dt.datetime.max)),
        ),
    ],
    Missions.Cryosat2: [
        Phase(
            "c2",
            ((7, 205), (133, 840)),
            Period(
                np.datetime64("2010-07-16"),
                np.datetime64("2020-08-01"),
                include_stop=False,
            ),
        ),
        Phase(
            "c2n",
            ((200, 1), None),
            period=Period(np.datetime64("2020-08-01"), np.datetime64(dt.datetime.max)),
        ),
    ],
    Missions.Envisat: [
        Phase(
            "en",
            ((6, 98), (93, 1002)),
            period=Period(
                np.datetime64("2002-05-17"),
                np.datetime64("2010-10-19"),
                include_stop=False,
            ),
        ),
        Phase(
            "enn",
            ((95, 818), (113, 533)),
            period=Period(
                np.datetime64("2010-10-26"),
                np.datetime64("2012-04-09"),
                include_stop=False,
            ),
        ),
    ],
    Missions.Ers1: [
        Phase(
            "e1",
            ((15, 1), (43, 27)),
            Period(
                np.datetime64("1992-10-23"),
                np.datetime64("1995-05-16"),
                include_stop=False,
            ),
        ),
        Phase(
            "e1g",
            ((30, 254), (40, 121)),
            Period(
                np.datetime64("1994-04-10"),
                np.datetime64("1995-03-22"),
                include_stop=False,
            ),
        ),
    ],
    Missions.Ers2: [
        Phase(
            "e2",
            ((1, 1), (74, 24)),
            Period(
                np.datetime64("1995-05-15"),
                np.datetime64("2002-05-15"),
                include_stop=False,
            ),
        )
    ],
    Missions.GeosatFollowOn: [
        Phase(
            "g2",
            ((37, 2), (222, 338)),
            Period(
                np.datetime64("2000-01-07"),
                np.datetime64("2008-09-08"),
                include_start=False,
            ),
        )
    ],
    Missions.Haiyang2A: [
        Phase(
            "h2a",
            ((67, 1), (117, 107)),
            Period(
                np.datetime64("2014-04-12"),
                np.datetime64("2016-03-16"),
                include_stop=False,
            ),
        ),
        Phase(
            "h2ag",
            ((118, 192), (288, 248)),
            Period(
                np.datetime64("2016-03-31"),
                np.datetime64("2020-06-10"),
                include_stop=False,
            ),
        ),
    ],
    Missions.Haiyang2B: [
        Phase(
            "h2b",
            ((30, 306), None),
            Period(np.datetime64("2019-12-20"), np.datetime64(dt.datetime.max)),
        )
    ],
    Missions.Haiyang2C: [
        Phase(
            "h2c",
            ((0, 0), None),
            Period(np.datetime64("2022-12-01"), np.datetime64(dt.datetime.max)),
        )
    ],
    Missions.Jason1: [
        Phase(
            "j1",
            ((11, 1), (249, 254)),
            Period(
                np.datetime64("2002-04-24"),
                np.datetime64("2008-10-20"),
                include_stop=False,
            ),
        ),
        Phase(
            "j1n",
            ((262, 13), (374, 173)),
            Period(
                np.datetime64("2009-02-10"),
                np.datetime64("2012-03-04"),
                include_stop=False,
            ),
        ),
        Phase(
            "j1g",
            ((500, 2), (535, 223)),
            Period(
                np.datetime64("2012-05-07"),
                np.datetime64("2013-06-02"),
                include_stop=False,
            ),
        ),
    ],
    Missions.Jason2: [
        Phase(
            "j2",
            ((10, 254), (290, 254)),
            Period(
                np.datetime64("2008-10-19"),
                np.datetime64("2016-05-27"),
                include_stop=False,
            ),
        ),
        Phase(
            "j2n",
            ((306, 1), (327, 111)),
            Period(
                np.datetime64("2016-10-17"),
                np.datetime64("2017-05-18"),
                include_stop=False,
            ),
        ),
        Phase(
            "j2g",
            ((500, 33), (506, 178)),
            Period(
                np.datetime64("2017-07-11"),
                np.datetime64("2017-09-15"),
                include_stop=False,
            ),
        ),
    ],
    Missions.Jason3: [
        Phase(
            "j3",
            ((11, 1), (216, 254)),
            Period(
                np.datetime64("2016-05-26"),
                np.datetime64("2021-12-30"),
                include_stop=False,
            ),
        ),
        Phase(
            "j3n",
            ((300, 159), (400, 84)),
            Period(
                np.datetime64("2022-04-25"),
                np.datetime64("2025-01-02"),
                include_stop=False,
            ),
        ),
        Phase(
            "j3g",
            ((600, 56), None),
            Period(np.datetime64("2025-06-19"), np.datetime64(dt.datetime.max)),
        ),
    ],
    Missions.Sentinel6A: [
        Phase(
            "s6a",
            ((41, 254), None),
            Period(np.datetime64("2021-12-29"), np.datetime64(dt.datetime.max)),
        )
    ],
    Missions.Sentinel3A: [
        Phase(
            "s3a",
            ((6, 1), None),
            Period(np.datetime64("2016-06-28"), np.datetime64(dt.datetime.max)),
        )
    ],
    Missions.Sentinel3B: [
        Phase(
            "s3b",
            ((19, 219), None),
            Period(np.datetime64("2018-11-27"), np.datetime64(dt.datetime.max)),
        )
    ],
    Missions.TopexPoseidon: [
        Phase(
            "tp",
            ((3, 2), (353, 254)),
            Period(
                np.datetime64("1992-10-13"),
                np.datetime64("2002-04-25"),
                include_stop=False,
            ),
        ),
        Phase(
            "tpn",
            ((368, 19), (480, 237)),
            Period(
                np.datetime64("2002-09-10"),
                np.datetime64("2005-10-04"),
                include_stop=False,
            ),
        ),
    ],
    Missions.Cfosat: [
        Phase(
            "cfo",
            ((0, 0), None),
            Period(np.datetime64("2018-11-03"), np.datetime64(dt.datetime.max)),
        )
    ],
}

_ALIASES = {
    "swonc": "calval",
    "swon": "science",
    "swot": "science",
    "s6a_hr": "s6a",
    "s6a_lr": "s6a",
}

_FLATTENED_PHASES = dict(
    map(
        lambda p: (p.short_name, p),
        functools.reduce(lambda x, y: x + y, PHASES.values()),
    )
)

for alias, key in _ALIASES.items():
    new = deepcopy(_FLATTENED_PHASES[key])
    new.short_name = alias
    _FLATTENED_PHASES[alias] = new

MissionsPhases = Enum("MissionsPhase", _FLATTENED_PHASES)
