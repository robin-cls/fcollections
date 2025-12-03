from __future__ import annotations

import typing as tp

import numpy as np
import pytest

from fcollections.implementations import (
    FileNameConventionERA5,
    NetcdfFilesDatabaseERA5,
)

if tp.TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "time, result_size",
    [
        (None, 2),
        (np.datetime64("2025-03-02"), 1),
    ],
)
def test_list_era5(era5_dir: Path, time: None | np.datetime64, result_size: int):
    db = NetcdfFilesDatabaseERA5(era5_dir)
    args = {}
    if time:
        args["time"] = time

    files = db.list_files(**args)
    assert files["filename"].size == result_size


def test_generate_string():
    conv = FileNameConventionERA5()
    t0 = np.datetime64("2024-09-25")
    assert conv.generate(time=t0) == "reanalysis-era5-single-levels_20240925.nc"
