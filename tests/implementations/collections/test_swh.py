from __future__ import annotations

import typing as tp

import numpy as np
import pytest

from fcollections.implementations import (
    FileNameConventionSWH,
    NetcdfFilesDatabaseSWH,
)
from fcollections.missions import MissionsPhases
from fcollections.time import Period

if tp.TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "params, result_size",
    [
        ({}, 3),
        ({"time": (np.datetime64("2025-03-08"), np.datetime64("2025-03-11"))}, 2),
        ({"mission": "s6a_lr"}, 2),
    ],
)
def test_list_wave(swh_dir: Path, params: dict[str, tp.Any], result_size: int):
    db = NetcdfFilesDatabaseSWH(swh_dir)

    files = db.list_files(**params)
    assert files["filename"].size == result_size


@pytest.mark.without_geo_packages
def test_query_bbox_disabled(swh_dir: Path):
    db = NetcdfFilesDatabaseSWH(swh_dir)
    with pytest.raises(ValueError):
        db.query(bbox=(-180, -90, 180, 90))


def test_generate_string():
    conv = FileNameConventionSWH()
    t0 = np.datetime64("2024-09-25")
    t1 = np.datetime64("2024-09-26")
    prod_date = np.datetime64("2024-09-30")
    assert (
        conv.generate(
            mission=MissionsPhases.swot, time=Period(t0, t1), production_date=prod_date
        )
        == "global_vavh_l3_rt_swot_20240925T000000_20240926T000000_20240930T000000.nc"
    )
