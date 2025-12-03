import os
import re
import typing as tp
from pathlib import Path

import numpy as np
import pandas as pda
import pytest

from fcollections.core import (
    FileDiscoverer,
    FileNameConvention,
    FileSystemIterable,
)
from fcollections.implementations import (
    CMEMS_NADIR_SSHA_LAYOUT,
    Delay,
    NetcdfFilesDatabaseL2Nadir,
    NetcdfFilesDatabaseL3Nadir,
    ProductLevel,
)
from fcollections.missions import MissionsPhases
from fcollections.time import Period


def test_bad_kwargs(l3_nadir_dir: Path):
    db = NetcdfFilesDatabaseL2Nadir(l3_nadir_dir)
    with pytest.raises(ValueError):
        db.list_files(bad_arg="bad_arg")
    with pytest.raises(ValueError):
        db.query(bad_arg="bad_arg")

    db = NetcdfFilesDatabaseL3Nadir(l3_nadir_dir)
    with pytest.raises(ValueError):
        db.list_files(bad_arg="bad_arg")
    with pytest.raises(ValueError):
        db.query(bad_arg="bad_arg")


@pytest.mark.parametrize(
    "time, mission, result_size",
    [
        (None, None, 3),
        ((np.datetime64("2023-10-14"), np.datetime64("2023-10-16")), None, 1),
        ((np.datetime64("2023-10-03"), np.datetime64("2023-10-16")), None, 2),
        (None, MissionsPhases.al, 1),
        (None, MissionsPhases.swonc, 2),
    ],
)
def test_list_l3_nadir(
    l3_nadir_dir: Path,
    time: None | np.datetime64,
    mission: None | MissionsPhases,
    result_size: int,
):

    db = NetcdfFilesDatabaseL3Nadir(l3_nadir_dir)
    args = {}
    if time:
        args["time"] = time
    if mission:
        args["mission"] = mission

    files = db.list_files(**args)
    assert files["filename"].size == result_size
    assert all(files["resolution"].values != None)


@pytest.mark.parametrize(
    "args, result_size",
    [
        ({}, 3),
        ({"time": (np.datetime64("2023-07-07"), np.datetime64("2023-07-08"))}, 2),
        ({"cycle_number": 575}, 2),
        ({"pass_number": 14}, 2),
        ({"cycle_number": 574, "pass_number": 15}, 0),
    ],
)
def test_list_l2_nadir(l2_nadir_dir: Path, args: dict[str, tp.Any], result_size: int):

    db = NetcdfFilesDatabaseL2Nadir(l2_nadir_dir)

    files = db.list_files(**args)
    assert files["filename"].size == result_size


@pytest.fixture
def parsing_result() -> pda.DataFrame:
    return pda.DataFrame(
        [
            (
                MissionsPhases.j3n,
                ProductLevel.L3,
                1,
                Period("2023-01-01", "2023-01-02", include_stop=False),
                np.datetime64("2023-01-03"),
                "nrt_1.nc",
            ),
            (
                MissionsPhases.j3n,
                ProductLevel.L3,
                1,
                Period("2023-01-01", "2023-01-02", include_stop=False),
                np.datetime64("2023-01-04"),
                "nrt_2.nc",
            ),
            (
                MissionsPhases.j3n,
                ProductLevel.L3,
                1,
                Period("2023-01-01", "2023-01-02", include_stop=False),
                np.datetime64("2023-01-05"),
                "nrt_3.nc",
            ),
            (
                MissionsPhases.j3n,
                ProductLevel.L3,
                None,
                Period("2023-01-01", "2023-01-02", include_stop=False),
                np.datetime64("2023-01-05"),
                "nrt_4.nc",
            ),
            (
                MissionsPhases.j3n,
                ProductLevel.L3,
                1,
                Period("2023-01-02", "2023-01-03", include_stop=False),
                np.datetime64("2023-01-06"),
                "nrt_5.nc",
            ),
            (
                MissionsPhases.j3n,
                ProductLevel.L3,
                1,
                Period("2023-01-02", "2023-01-03", include_stop=False),
                np.datetime64("2023-01-07"),
                "nrt_6.nc",
            ),
            (
                MissionsPhases.al,
                ProductLevel.L3,
                1,
                Period("2023-01-01", "2023-01-02", include_stop=False),
                np.datetime64("2023-01-04"),
                "nrt_7.nc",
            ),
            (
                MissionsPhases.al,
                ProductLevel.L3,
                1,
                Period("2023-01-01", "2023-01-02", include_stop=False),
                np.datetime64("2023-01-05"),
                "nrt_8.nc",
            ),
        ],
        columns=[
            "mission",
            "product_level",
            "resolution",
            "time",
            "production_date",
            "filename",
        ],
    )


def test_deduplicate_error_two_missions(
    l3_nadir_dir: Path, parsing_result: pda.DataFrame
):
    db = NetcdfFilesDatabaseL3Nadir(l3_nadir_dir)
    with pytest.raises(ValueError):
        db.unmixer(parsing_result)


def test_validate(l3_nadir_dir: Path, parsing_result: pda.DataFrame):
    db = NetcdfFilesDatabaseL3Nadir(l3_nadir_dir)
    df_sub = parsing_result[
        (parsing_result["mission"] == MissionsPhases.j3n)
        & (parsing_result["resolution"] == 1)
    ].copy()
    df_result = db.unmixer(df_sub)
    df_result = db.deduplicator(df_sub)
    assert parsing_result.iloc[[2, 5]].reset_index(drop=True).equals(df_result)


@pytest.mark.parametrize(
    "mission, delay, expected",
    [
        (
            MissionsPhases.j3g,
            Delay.NRT,
            "/SEALEVEL_GLO_PHY_L3_NRT_008_044/cmems_obs-sl_glo_phy-ssh_nrt_j3g-l3-duacs_PT1S_202411/1995/05",
        ),
        # Test the _ -> - conversion in layout generation
        (
            MissionsPhases.s6a_hr,
            Delay.MY,
            "/SEALEVEL_GLO_PHY_L3_NRT_008_044/cmems_obs-sl_glo_phy-ssh_my_s6a-hr-l3-duacs_PT1S_202411/1995/05",
        ),
    ],
)
def test_generate_layout(mission: MissionsPhases, delay: Delay, expected: str):
    path = CMEMS_NADIR_SSHA_LAYOUT.generate(
        "/SEALEVEL_GLO_PHY_L3_NRT_008_044",
        year=1995,
        month=5,
        resolution=1,
        delay=delay,
        version="202411",
        mission=mission,
    )

    assert path == expected


@pytest.mark.parametrize(
    "filters, expected",
    [
        ({"version": "202512"}, [1, 5]),
        ({"year": 2025}, [1]),
        ({"month": 6}, [0, 2, 3, 4, 5, 6]),
    ],
)
def test_layout_l3(
    l3_nadir_dir_layout: Path,
    expected: list[int],
    filters: dict[str, tp.Any],
    l3_nadir_files: list[str],
):
    """Test layout filters not integrated in the database."""
    fd = FileDiscoverer(
        FileNameConvention(re.compile(r".*"), []),
        FileSystemIterable(layout=CMEMS_NADIR_SSHA_LAYOUT),
    )

    actual = {
        os.path.basename(f) for f in fd.list(l3_nadir_dir_layout, **filters).filename
    }
    expected = {os.path.basename(l3_nadir_files[ii]) for ii in expected}
    assert len(expected) > 0
    assert expected == actual


@pytest.mark.parametrize(
    "filters",
    [
        {},
        {"delay": "NRT"},
        {"mission": "s3a"},
        {"resolution": 5},
    ],
)
def test_list_l3_layout(l3_nadir_dir_layout: Path, filters: dict[str, tp.Any]):
    db = NetcdfFilesDatabaseL3Nadir(l3_nadir_dir_layout, layout=CMEMS_NADIR_SSHA_LAYOUT)
    db_no_layout = NetcdfFilesDatabaseL3Nadir(l3_nadir_dir_layout)

    actual = db.list_files(**filters)
    expected = db_no_layout.list_files(**filters)
    assert len(expected) > 0
    assert expected.equals(actual)


@pytest.mark.with_geo_packages
def test_query_bbox(l3_nadir_dir: Path):
    db = NetcdfFilesDatabaseL3Nadir(l3_nadir_dir)

    ds = db.query(mission="al")
    assert ds.time.size == 4

    ds = db.query(mission="al", bbox=(300, -90, 360, 90))
    assert ds.time.size == 2


@pytest.mark.without_geo_packages
def test_query_bbox_disabled(l3_nadir_dir_layout: Path):
    db = NetcdfFilesDatabaseL3Nadir(l3_nadir_dir_layout)
    with pytest.raises(ValueError):
        db.query(bbox=(-180, -90, 180, 90))
