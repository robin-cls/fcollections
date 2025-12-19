import os
import typing as tp
from pathlib import Path

import numpy as np
import pandas as pda
import pytest
from fsspec.implementations.local import LocalFileSystem

from fcollections.core import FileSystemMetadataCollector
from fcollections.implementations import (
    CMEMS_SSHA_L3_LAYOUT,
    Delay,
    NetcdfFilesDatabaseL3Nadir,
    ProductLevel,
)
from fcollections.implementations._definitions._cmems import (
    Area,
    DataType,
    Group,
    Origin,
    ProductClass,
    Thematic,
    Typology,
    Variable,
)
from fcollections.missions import MissionsPhases
from fcollections.time import ISODuration, Period


def test_bad_kwargs(l3_nadir_dir: Path):
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


class TestLayout:

    @pytest.mark.parametrize(
        "dataset_id",
        [
            # SEALEVEL_GLO_PHY_L3_MY_008_062
            "cmems_obs-sl_glo_phy-ssh_my_c2-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_c2n-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_en-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_enn-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_e1-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_e1g-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_e2-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_g2-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_h2a-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_h2ag-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_h2b-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_j1-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_j1g-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_j1n-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_j2-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_j2n-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_j2g-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_j3-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_j3n-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_j3g-l3-duacs_PT1S-i",
            "cmems_obs-sl_glo_phy-ssh_my_al-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_alg-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_s3a-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_s3b-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_s6a-lr-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_swon-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_swonc-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_tp-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_my_tpn-l3-duacs_PT1S",
            # SEALEVEL_GLO_PHY_L3_NRT_008_044
            "cmems_obs-sl_glo_phy-ssh_nrt_c2n-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_nrt_h2b-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_nrt_h2b-l3-duacs_PT0.2S",
            "cmems_obs-sl_glo_phy-ssh_nrt_j3n-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_nrt_j3n-l3-duacs_PT0.2S",
            "cmems_obs-sl_glo_phy-ssh_nrt_j3g-l3-duacs_PT1S-i",
            "cmems_obs-sl_glo_phy-ssh_nrt_j3g-l3-duacs_PT0.2S-i",
            "cmems_obs-sl_glo_phy-ssh_nrt_al-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_nrt_s3a-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_nrt_s3a-l3-duacs_PT0.2S",
            "cmems_obs-sl_glo_phy-ssh_nrt_s3b-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_nrt_s3b-l3-duacs_PT0.2S",
            "cmems_obs-sl_glo_phy-ssh_nrt_s6a-hr-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_nrt_s6a-hr-l3-duacs_PT0.2S",
            "cmems_obs-sl_glo_phy-ssh_nrt_swon-l3-duacs_PT1S",
            "cmems_obs-sl_glo_phy-ssh_nrt_swon-l3-duacs_PT0.2S"
            # Output of get original files
            "cmems_obs-sl_glo_phy-ssh_nrt_j3g-l3-duacs_PT0.2S-i_202411",
        ],
    )
    def test_dataset_id_regex(self, dataset_id: str):
        """Check dataset id convention building."""
        actual = CMEMS_SSHA_L3_LAYOUT.conventions[0].match(dataset_id)
        assert actual is not None

    @pytest.mark.parametrize(
        "expected, version, mission, data_type, resolution, typology",
        [
            (
                "cmems_obs-sl_glo_phy-ssh_my_e2-l3-duacs_PT0.2S_202411",
                "202411",
                MissionsPhases.e2,
                DataType.MY,
                ISODuration(seconds=0.2),
                None,
            ),
            (
                "cmems_obs-sl_glo_phy-ssh_nrt_c2n-l3-duacs_PT1S-i",
                None,
                MissionsPhases.c2n,
                DataType.NRT,
                ISODuration(seconds=1),
                Typology.I,
            ),
            (
                "cmems_obs-sl_glo_phy-ssh_nrt_s3b-l3-duacs_PT1S",
                None,
                MissionsPhases.s3b,
                DataType.NRT,
                ISODuration(seconds=1),
                None,
            ),
            (
                "cmems_obs-sl_glo_phy-ssh_nrt_j3g-l3-duacs_PT0.2S-i_202411",
                "202411",
                MissionsPhases.j3g,
                DataType.NRT,
                ISODuration(seconds=0.2),
                Typology.I,
            ),
        ],
    )
    def test_dataset_id_generate(
        self,
        expected: str,
        version: str | None,
        resolution: float,
        mission: MissionsPhases,
        data_type: DataType,
        typology: Typology | None,
    ):
        dataset_id = CMEMS_SSHA_L3_LAYOUT.conventions[0].generate(
            resolution=resolution,
            mission=mission,
            origin=Origin.CMEMS,
            group=Group.OBS,
            pc=ProductClass.SL,
            area=Area.GLO,
            thematic=Thematic.PHY,
            variable=Variable.SSH,
            type=data_type,
            temporal_resolution=resolution,
            typology=typology,
            version=version,
        )

        assert dataset_id == expected

    @pytest.mark.parametrize(
        "mission, delay, expected",
        [
            (
                MissionsPhases.j3g,
                Delay.NRT,
                "/SEALEVEL_GLO_PHY_L3_NRT_008_044/cmems_obs-sl_glo_phy-ssh_nrt_j3g-l3-duacs_PT1S_202411/1995/05/nrt_global_j3g_phy_L3_1hz_19950501_20240101",
            ),
            # Test the _ -> - conversion in layout generation
            (
                MissionsPhases.s6a_hr,
                Delay.MY,
                "/SEALEVEL_GLO_PHY_L3_NRT_008_044/cmems_obs-sl_glo_phy-ssh_my_s6a-hr-l3-duacs_PT1S_202411/1995/05/my_global_s6a_hr_phy_L3_1hz_19950501_20240101",
            ),
        ],
    )
    def test_generate_layout(
        self, mission: MissionsPhases, delay: Delay, expected: str
    ):
        period = Period(
            np.datetime64("1995-05-01"), np.datetime64("1995-05-02"), include_stop=False
        )
        path = CMEMS_SSHA_L3_LAYOUT.generate(
            "/SEALEVEL_GLO_PHY_L3_NRT_008_044",
            year=1995,
            month=5,
            resolution=1,
            temporal_resolution=ISODuration(seconds=1),
            delay=delay,
            version="202411",
            mission=mission,
            origin=Origin.CMEMS,
            group=Group.OBS,
            pc=ProductClass.SL,
            area=Area.GLO,
            thematic=Thematic.PHY,
            variable=Variable.SSH,
            typology=None,
            type=delay,
            product_level=ProductLevel.L3,
            production_date=np.datetime64("2024-01-01"),
            time=period,
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
        self,
        l3_nadir_dir_layout: Path,
        expected: list[int],
        filters: dict[str, tp.Any],
        l3_nadir_files: list[str],
    ):
        """Test layout filters not integrated in the database."""
        collector = FileSystemMetadataCollector(
            l3_nadir_dir_layout, NetcdfFilesDatabaseL3Nadir.layouts, LocalFileSystem()
        )

        actual = {
            os.path.basename(f) for f in collector.to_dataframe(**filters).filename
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
    def test_list_l3_layout(
        self,
        l3_nadir_dir_layout: Path,
        l3_nadir_dir_no_layout: Path,
        filters: dict[str, tp.Any],
    ):
        db = NetcdfFilesDatabaseL3Nadir(l3_nadir_dir_layout)
        db_no_layout = NetcdfFilesDatabaseL3Nadir(l3_nadir_dir_no_layout)

        # Duplicates in the sort key (unmix set to False allows this). Need to
        # test the tuples because dataframe order is not ensured
        actual = db.list_files(**filters).drop(columns=["filename"])
        expected = db_no_layout.list_files(**filters).drop(columns=["filename"])

        assert len(expected) > 0
        assert set(map(tuple, actual.to_numpy())) == set(
            map(tuple, expected.to_numpy())
        )


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
