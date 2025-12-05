from __future__ import annotations

import typing as tp

import numpy as np
import pytest

from fcollections.implementations import (
    FileNameConventionSST,
    NetcdfFilesDatabaseSST,
)

if tp.TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "time, result_size",
    [
        (None, 2),
        ((np.datetime64("2023-10-16"), np.datetime64("2023-10-17")), 1),
        ((np.datetime64("2023-10-16"), np.datetime64("2023-10-30")), 2),
    ],
)
def test_list_sst(sst_dir: Path, time: None | np.datetime64, result_size: int):

    db = NetcdfFilesDatabaseSST(sst_dir)
    args = {}
    if time:
        args["time"] = time

    files = db.list_files(**args)
    assert files["filename"].size == result_size


@pytest.mark.without_geo_packages
def test_query_bbox_disabled(sst_dir: Path):
    db = NetcdfFilesDatabaseSST(sst_dir)
    with pytest.raises(ValueError):
        db.query(bbox=(-180, -90, 180, 90))


def test_generate_string():
    conv = FileNameConventionSST()
    t = np.datetime64("2024-09-25T00")
    assert (
        conv.generate(time=t)
        == "20240925000000-IFR-L3S_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v02.1-fv01.0.nc"
    )
