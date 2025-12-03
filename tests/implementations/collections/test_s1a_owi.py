from __future__ import annotations

import typing as tp

import numpy as np
import pytest

from fcollections.implementations import (
    AcquisitionMode,
    FileNameConventionS1AOWI,
    NetcdfFilesDatabaseS1AOWI,
    S1AOWIProductType,
    S1AOWISlicePostProcessing,
)
from fcollections.time import Period

if tp.TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "params, result_size",
    [
        ({}, 2),
        ({"acquisition_mode": AcquisitionMode.EW}, 0),
        ({"acquisition_mode": AcquisitionMode.IW}, 2),
        ({"slice_post_processing": S1AOWISlicePostProcessing.OCN}, 1),
        ({"time": (np.datetime64("2024-09-24T11:21"), None)}, 1),
        ({"resolution": 3}, 2),
        ({"orbit": 55807}, 1),
        ({"product_type": S1AOWIProductType.SW}, 1),
    ],
)
def test_list_s1aowi(s1aowi_dir: Path, params: dict[str, tp.Any], result_size: int):
    db = NetcdfFilesDatabaseS1AOWI(s1aowi_dir)

    files = db.list_files(**params)
    assert files["filename"].size == result_size


def test_generate_string():
    conv = FileNameConventionS1AOWI()
    t0 = np.datetime64("2024-09-25")
    t1 = np.datetime64("2024-09-26")
    assert (
        conv.generate(
            acquisition_mode=AcquisitionMode.IW,
            slice_post_processing=S1AOWISlicePostProcessing.CC,
            time=Period(t0, t1),
            resolution=11,
            orbit=2124,
            product_type=S1AOWIProductType.GS,
        )
        == "s1a-iw-owi-cc-20240925t000000-20240926t000000-000011-002124_gs.nc"
    )
