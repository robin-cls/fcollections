from __future__ import annotations

import typing as tp

import numpy as np
import pytest

from fcollections.implementations import (
    CMEMS_SWH_LAYOUT,
    FileNameConventionSWH,
    NetcdfFilesDatabaseSWH,
)
from fcollections.implementations._definitions._cmems import Sensors
from fcollections.time import Period

if tp.TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "params, result_size",
    [
        ({}, 3),
        ({"time": (np.datetime64("2025-03-08"), np.datetime64("2025-03-11"))}, 2),
        ({"sensorf": "S6A_LR"}, 2),
    ],
)
@pytest.mark.parametrize("dir_name", ["swh_dir_flat", "swh_dir_layout"])
def test_list_wave(
    dir_name: str,
    params: dict[str, tp.Any],
    result_size: int,
    request: pytest.FixtureRequest,
):
    swh_dir = request.getfixturevalue(dir_name)
    db = NetcdfFilesDatabaseSWH(swh_dir)

    files = db.list_files(**params)
    assert files["filename"].size == result_size


@pytest.mark.without_geo_packages
def test_query_bbox_disabled(swh_dir_flat: Path):
    db = NetcdfFilesDatabaseSWH(swh_dir_flat)
    with pytest.raises(ValueError):
        db.query(bbox=(-180, -90, 180, 90))


def test_generate_string():
    conv = FileNameConventionSWH()
    t0 = np.datetime64("2024-09-25")
    t1 = np.datetime64("2024-09-26")
    prod_date = np.datetime64("2024-09-30")
    assert (
        conv.generate(
            sensorf=Sensors.SWOT, time=Period(t0, t1), production_date=prod_date
        )
        == "global_vavh_l3_rt_swot_20240925T000000_20240926T000000_20240930T000000.nc"
    )


@pytest.mark.parametrize(
    "dataset_id",
    [
        # WAVE_GLO_PHY_SWH_L3_NRT_014_001
        "cmems_obs-wave_glo_phy-swh_nrt_cfo-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_c2-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_h2b-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_h2c-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_j3-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_al-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_s3a-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_s3b-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_s6a-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_swon-l3_PT1S",
    ],
)
def test_dataset_id(dataset_id: str):
    actual = CMEMS_SWH_LAYOUT.conventions[0].regex.match(dataset_id)
    assert actual is not None
