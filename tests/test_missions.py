import datetime as dt

import numpy as np

from fcollections.missions import MissionsPhases, Phase
from fcollections.time import Period


def test_ongoing():
    phase = Phase(
        "tt",
        ((1, 1), None),
        Period(np.datetime64("2024-01-01"), np.datetime64(dt.datetime.max)),
    )

    assert phase.on_going
    assert phase.period.intersects(np.datetime64(dt.datetime.now()))
    assert phase.cycles == (1, None)


def test_historic():
    phase = Phase(
        "tt",
        ((400, 3), (450, 4)),
        Period(np.datetime64("2024-01-01"), np.datetime64("2024-02-01")),
    )
    assert phase.cycles == (400, 450)
    assert not phase.period.intersects(np.datetime64(dt.datetime.now()))
    assert not phase.on_going


def test_mission_phases():
    assert {e.name for e in MissionsPhases} == {
        "al",
        "alg",
        "cfo",
        "c2",
        "c2n",
        "e1g",
        "e1",
        "e2",
        "en",
        "enn",
        "g2",
        "h2ag",
        "h2a",
        "h2b",
        "h2c",
        "j1",
        "j1g",
        "j1n",
        "j2",
        "j2g",
        "j2n",
        "j3",
        "j3n",
        "j3g",
        "s3a",
        "s3b",
        "s6a",
        "s6a_lr",
        "s6a_hr",
        "swon",
        "swonc",
        "swot",
        "calval",
        "science",
        "tp",
        "tpn",
    }
