from __future__ import annotations

import typing as tp

import numpy as np
import pytest

from fcollections.implementations import (
    CMEMS_SST_LAYOUT,
    IFREMER_SST_LAYOUT,
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
@pytest.mark.parametrize(
    "dir_name",
    [
        "sst_dir_flat",
        "sst_dir_layout",
        "sst_dir_layout2",
    ],
)
def test_list_sst(
    dir_name: str,
    time: None | np.datetime64,
    result_size: int,
    request: pytest.FixtureRequest,
):
    sst_dir = request.getfixturevalue(dir_name)
    db = NetcdfFilesDatabaseSST(sst_dir)
    args = {}
    if time:
        args["time"] = time

    files = db.list_files(**args)
    assert files["filename"].size == result_size


@pytest.mark.without_geo_packages
def test_query_bbox_disabled(sst_dir_flat: Path):
    db = NetcdfFilesDatabaseSST(sst_dir_flat)
    with pytest.raises(ValueError):
        db.query(bbox=(-180, -90, 180, 90))


def test_generate_string():
    conv = FileNameConventionSST()
    t = np.datetime64("2024-09-25T00")
    assert (
        conv.generate(time=t)
        == "20240925000000-IFR-L3S_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v02.1-fv01.0.nc"
    )


@pytest.mark.parametrize(
    "dataset_id",
    [
        # SST_GLO_SST_L3S_NRT_OBSERVATIONS_010_010
        "cmems_obs-sst_glo_phy_l3s_gir_P1D-m",
        "IFREMER-GLOB-SST-L3-NRT-OBS_FULL_TIME_SERIE",
        "cmems_obs-sst_glo_phy_l3s_pir_P1D-m",
        "cmems_obs-sst_glo_phy_l3s_pmw_P1D-m",
    ],
)
def test_dataset_id(dataset_id: str):
    actual = CMEMS_SST_LAYOUT.conventions[0].regex.match(dataset_id)
    actual2 = IFREMER_SST_LAYOUT.conventions[0].regex.match(dataset_id)
    assert actual is not None or actual2 is not None
