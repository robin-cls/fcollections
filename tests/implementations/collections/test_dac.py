from __future__ import annotations

import typing as tp

import numpy as np
import pytest

from fcollections.implementations import (
    FileNameConventionDAC,
    NetcdfFilesDatabaseDAC,
)

if tp.TYPE_CHECKING:
    from pathlib import Path

    import numpy.typing as np_t


@pytest.fixture
def expected_times() -> np_t.NDArray[np.datetime64]:
    return np.array(
        ["2023-01-02T12", "2023-01-04", "2023-01-05T12", "2023-01-05T18"], dtype="M8"
    )


@pytest.mark.parametrize(
    "time, result_slice",
    [
        (None, slice(0, None)),
        (("2023-01-03", "2023-01-07"), slice(1, None)),
    ],
)
def test_list_dac(
    dac_dir: Path,
    expected_times: np_t.NDArray[np.datetime64],
    time: bool,
    result_slice: slice,
):
    db = NetcdfFilesDatabaseDAC(dac_dir)
    args = {}
    if time:
        args["time"] = time

    files = db.list_files(**args, sort=True)
    assert np.array_equal(files["time"].values, expected_times[result_slice])


@pytest.mark.without_geo_packages
def test_query_bbox_disabled(dac_dir: Path):
    db = NetcdfFilesDatabaseDAC(dac_dir)
    with pytest.raises(ValueError):
        db.query(bbox=(-180, -90, 180, 90))


def test_generate_string():
    conv = FileNameConventionDAC()
    assert conv.generate(time=np.datetime64("2023-01-03")) == "dac_dif_26665_00.nc"
