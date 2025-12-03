from __future__ import annotations

import typing as tp

import numpy as np
import pytest

from fcollections.time import Period, times_holes

if tp.TYPE_CHECKING:
    import numpy.typing as np_t


@pytest.fixture(scope="session")
def times() -> np_t.NDArray[np.datetime64]:
    return np.arange("2024-01-01T00", "2024-01-01T12", dtype="M8[h]")


@pytest.fixture(scope="session")
def delta() -> np.timedelta64:
    return np.timedelta64(1, "h")


@pytest.mark.parametrize(
    "removed_indexes, expected_holes",
    [
        ([1], [("2024-01-01T00", "2024-01-01T02")]),
        ([10], [("2024-01-01T09", "2024-01-01T11")]),
        ([0], []),
        ([11], []),
        ([2, 3], [("2024-01-01T01", "2024-01-01T04")]),
    ],
)
def test_times_holes(
    times: np_t.NDArray[np.datetime64],
    delta: np.timedelta64,
    removed_indexes: list[int],
    expected_holes: list[tuple[str, str]],
):
    selected_indexes = list(
        filter(lambda x: x not in removed_indexes, np.arange(len(times)))
    )
    actual_holes = list(times_holes(times[selected_indexes], delta))
    expected_holes = [
        Period(
            np.datetime64(x[0]),
            np.datetime64(x[1]),
            include_start=False,
            include_stop=False,
        )
        for x in expected_holes
    ]

    assert actual_holes == expected_holes


@pytest.mark.parametrize(
    "jitter, expected_holes",
    [
        ([5, -5, 5, -5, 5, -5, 5, -5, 5, -5, 5, -5], []),
        (
            [5, -50, 5, -5, 5, -5, 40, -10, 45, -5, 5, -5],
            [
                ("2024-01-01T00:30:00", "2024-01-01T02:03:00"),
                ("2024-01-01T06:54:00", "2024-01-01T08:27:00"),
            ],
        ),
    ],
)
def test_times_holes_jitter(
    times: np_t.NDArray[np.datetime64],
    delta: np.timedelta64,
    jitter: list[float],
    expected_holes: list[tuple[str, str]],
):

    new_times = times + np.array(jitter, dtype=float) * 0.01 * delta.astype("m8[s]")

    actual_holes = list(times_holes(new_times, delta))
    expected_holes = [
        Period(
            np.datetime64(x[0]),
            np.datetime64(x[1]),
            include_start=False,
            include_stop=False,
        )
        for x in expected_holes
    ]

    assert actual_holes == expected_holes
