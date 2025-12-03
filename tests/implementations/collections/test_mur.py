from __future__ import annotations

import typing as tp

import numpy as np
import pytest

from fcollections.implementations import (
    FileNameConventionMUR,
    NetcdfFilesDatabaseMUR,
)

if tp.TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "time, result_size",
    [
        (None, 2),
        (np.datetime64("2025-03-09T09:00:00"), 1),
        ((np.datetime64("2025-03-05"), np.datetime64("2025-03-10")), 2),
    ],
)
def test_list_mur(mur_dir: Path, time: None | np.datetime64, result_size: int):
    db = NetcdfFilesDatabaseMUR(mur_dir)
    args = {}
    if time:
        args["time"] = time

    files = db.list_files(**args)
    assert files["filename"].size == result_size


@pytest.mark.without_geo_packages
def test_query_bbox_disabled(mur_dir: Path):
    db = NetcdfFilesDatabaseMUR(mur_dir)
    with pytest.raises(ValueError):
        db.query(bbox=(-180, -90, 180, 90))


def test_generate_string():
    conv = FileNameConventionMUR()
    t0 = np.datetime64("2024-09-25")
    assert (
        conv.generate(time=t0)
        == "20240925000000-JPL-L4_GHRSST-SSTfnd-MUR-GLOB-v02.0-fv04.1.nc"
    )
