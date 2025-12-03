from typing import List

import numpy as np
import pytest

from fcollections.time import (
    Period,
    fuse_successive_periods,
    periods_envelop,
    periods_holes,
)


@pytest.fixture
def periods() -> List[Period]:
    days = np.arange(np.datetime64("2023-01-16"), np.datetime64("2023-07-11"))
    holes = np.array(
        [
            "2023-04-24",
            "2023-05-01",
            "2023-05-02",
            "2023-05-03",
            "2023-05-20",
            "2023-05-21",
            "2023-06-10",
        ],
        dtype=np.datetime64,
    )
    mask = ~np.isin(days[:-1], holes)
    periods = np.array(
        [
            Period(days[ii], days[ii + 1], include_stop=False)
            for ii in range(len(days) - 1)
        ]
    )
    return list(periods[mask])


@pytest.fixture
def reduced_periods() -> List[Period]:
    return [
        Period(
            np.datetime64("2023-01-16"), np.datetime64("2023-04-24"), include_stop=False
        ),
        Period(
            np.datetime64("2023-04-25"), np.datetime64("2023-05-01"), include_stop=False
        ),
        Period(
            np.datetime64("2023-05-04"), np.datetime64("2023-05-20"), include_stop=False
        ),
        Period(
            np.datetime64("2023-05-22"), np.datetime64("2023-06-10"), include_stop=False
        ),
        Period(
            np.datetime64("2023-06-11"), np.datetime64("2023-07-10"), include_stop=False
        ),
    ]


@pytest.fixture
def holes() -> List[Period]:
    return [
        Period(
            np.datetime64("2023-04-24"), np.datetime64("2023-04-25"), include_stop=False
        ),
        Period(
            np.datetime64("2023-05-01"), np.datetime64("2023-05-04"), include_stop=False
        ),
        Period(
            np.datetime64("2023-05-20"), np.datetime64("2023-05-22"), include_stop=False
        ),
        Period(
            np.datetime64("2023-06-10"), np.datetime64("2023-06-11"), include_stop=False
        ),
    ]


def test_fuse_successive_periods(periods: List[Period], reduced_periods: List[Period]):
    assert reduced_periods == fuse_successive_periods(periods)


def test_envelop(periods: List[Period]):
    expected = Period(
        np.datetime64("2023-01-16"), np.datetime64("2023-07-10"), include_stop=False
    )
    assert expected == periods_envelop(periods)


def test_holes(reduced_periods: List[Period], holes: List[Period]):
    assert holes == list(periods_holes(reduced_periods))
