from __future__ import annotations

import typing as tp

import numpy as np
import pytest

from fcollections.implementations import NetcdfFilesDatabaseOHC

if tp.TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "params, result_size",
    [
        ({}, 1),
        ({"time": (np.datetime64("2024-09-26"), np.datetime64("2024-09-27"))}, 1),
    ],
)
def test_list_ohc(ohc_dir: Path, params: dict[str, tp.Any], result_size: int):
    db = NetcdfFilesDatabaseOHC(ohc_dir)

    files = db.list_files(**params)
    assert files["filename"].size == result_size


@pytest.mark.without_geo_packages
def test_query_bbox_disabled(ohc_dir: Path):
    db = NetcdfFilesDatabaseOHC(ohc_dir)
    with pytest.raises(ValueError):
        db.query(bbox=(-180, -90, 180, 90))
