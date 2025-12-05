from __future__ import annotations

import typing as tp

import numpy as np
import pytest

from fcollections.implementations import (
    Delay,
    NetcdfFilesDatabaseOC,
    OCVariable,
    ProductLevel,
    Sensor,
)

if tp.TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "params, result_size",
    [
        ({}, 4),
        ({"time": np.datetime64("2025-03-03")}, 1),
        ({"delay": Delay.NRT}, 1),
        ({"level": ProductLevel.L3}, 2),
        ({"sensor": Sensor.MULTI}, 2),
        ({"oc_variable": OCVariable.OPTICS}, 1),
        ({"spatial_resolution": "1km"}, 1),
        ({"temporal_resolution": "P1M"}, 1),
    ],
)
def test_list_chl(chl_dir: Path, params: dict[str, tp.Any], result_size: int):
    db = NetcdfFilesDatabaseOC(chl_dir)

    files = db.list_files(**params)
    assert files["filename"].size == result_size

    ds = db.query(**params)


@pytest.mark.without_geo_packages
def test_query_bbox_disabled(chl_dir: Path):
    db = NetcdfFilesDatabaseOC(chl_dir)
    with pytest.raises(ValueError):
        db.query(bbox=(-180, -90, 180, 90))
