from __future__ import annotations

import os
import typing as tp

import numpy as np
import pytest
from fsspec.implementations.local import LocalFileSystem

from fcollections.core import FileSystemMetadataCollector
from fcollections.implementations import (
    AVISO_L4_SWOT_LAYOUT,
    Delay,
    FileNameConventionGriddedSLA,
    FileNameConventionGriddedSLAInternal,
    NetcdfFilesDatabaseGriddedSLA,
)
from fcollections.missions import MissionsPhases
from fcollections.time import Period

if tp.TYPE_CHECKING:
    from pathlib import Path


class TestConvention:

    convention = FileNameConventionGriddedSLA()
    convention_internal = FileNameConventionGriddedSLAInternal()

    def test_internal_convention_generate(self):

        reference = "msla_oer_merged_h_27029.nc"
        period = Period(np.datetime64("2024-01-02"), np.datetime64("2024-01-03"))
        actual = self.convention_internal.generate(date=period)
        assert actual == reference

    def test_internal_convention_parse(self):
        filename = "msla_oer_merged_h_27029.nc"
        reference = (
            Period(
                np.datetime64("2024-01-02"),
                np.datetime64("2024-01-03"),
                include_stop=False,
            ),
        )
        actual = self.convention_internal.parse(
            self.convention_internal.match(filename)
        )
        assert actual == reference

    def test_convention_generate(self):

        reference = "dt_global_allsat_phy_l4_20230328_20250331.nc"
        actual = self.convention.generate(
            delay=Delay.DT,
            time=Period(
                np.datetime64("2023-03-28"),
                np.datetime64("2023-03-29"),
                include_stop=False,
            ),
            production_date=np.datetime64("2025-03-31"),
        )
        assert actual == reference

    def test_convention_parse(self):
        filename = "dt_global_allsat_phy_l4_20230328_20250331.nc.nc"
        reference = (
            Delay.DT,
            Period(
                np.datetime64("2023-03-28"),
                np.datetime64("2023-03-29"),
                include_stop=False,
            ),
            np.datetime64("2025-03-31"),
        )
        actual = self.convention.parse(self.convention.match(filename))
        assert actual == reference


class TestListing:

    @pytest.mark.parametrize(
        "params, result_size",
        [
            ({}, 3),
            ({"time": np.datetime64("2023-10-16")}, 2),
            ({"production_date": np.datetime64("2023-11-06")}, 1),
            ({"delay": Delay.NRT}, 2),
        ],
    )
    def test_list_gridded_sla(
        self, l4_ssha_dir_no_layout: Path, params: dict[str, tp.Any], result_size: int
    ):
        db = NetcdfFilesDatabaseGriddedSLA(l4_ssha_dir_no_layout)

        files = db.list_files(**params)
        assert files["filename"].size == result_size


class TestQuery:

    def test_bad_kwargs(self, l4_ssha_dir_no_layout: Path):
        db = NetcdfFilesDatabaseGriddedSLA(l4_ssha_dir_no_layout)
        with pytest.raises(ValueError):
            db.list_files(bad_arg="bad_arg")
        with pytest.raises(ValueError):
            db.query(bad_arg="bad_arg")

    @pytest.mark.without_geo_packages
    def test_query_bbox_disabled(self, l4_ssha_dir_no_layout: Path):
        db = NetcdfFilesDatabaseGriddedSLA(l4_ssha_dir_no_layout)
        with pytest.raises(ValueError):
            db.query(bbox=(-180, -90, 180, 90))


class TestLayout:

    def test_generate_layout_aviso(self):
        path = AVISO_L4_SWOT_LAYOUT.generate(
            "/duacs-experimental/dt-phy-grids/l4_karin_nadir",
            method="miost",
            version="1.0",
            phase=MissionsPhases.science,
            delay=Delay.NRT,
            time=Period(
                np.datetime64("2025-03-31"),
                np.datetime64("2025-04-01"),
                include_stop=False,
            ),
            production_date=np.datetime64("2025-03-31"),
        )

        assert (
            path
            == "/duacs-experimental/dt-phy-grids/l4_karin_nadir/v1.0/miost/science/nrt_global_allsat_phy_l4_20250331_20250331.nc"
        )

    @pytest.mark.parametrize(
        "filters, expected",
        [
            ({}, [0, 1, 2, 3, 4]),
            ({"version": "0.3"}, [2, 3, 4]),
            ({"method": "4dvarnet"}, [2]),
            ({"phase": "science"}, [0, 1]),
            ({"time": np.datetime64("2023-07-29")}, [1, 2, 3, 4]),
            ({"production_date": np.datetime64("2024-09-13")}, [2]),
            ({"delay": Delay.NRT}, [4]),
        ],
    )
    def test_list_layout_aviso(
        self,
        l4_ssha_dir_layout_aviso: Path,
        l4_ssha_files: list[str],
        expected: list[int],
        filters: dict[str, tp.Any],
    ):

        collector = FileSystemMetadataCollector(
            l4_ssha_dir_layout_aviso,
            NetcdfFilesDatabaseGriddedSLA.layouts,
            LocalFileSystem(),
        )

        actual = {
            os.path.basename(f) for f in collector.to_dataframe(**filters).filename
        }
        expected = {os.path.basename(l4_ssha_files[ii]) for ii in expected}
        assert len(expected) > 0
        assert expected == actual

    @pytest.mark.parametrize(
        "filters, expected",
        [
            ({}, [8, 9, 10, 11]),
            ({"delay": Delay.DT}, [0]),
            ({"delay_nrt_my": Delay.MY}, [0]),
            ({"version": "202411"}, [11]),
            ({"time": np.datetime64("2023-07-28")}, [8, 11]),
            ({"production_date": np.datetime64("2024-09-13")}, [10]),
            ({"spatial_resolution": 0.5}, [10]),
            ({"temporal_resolution": 0.5}, [9]),
        ],
    )
    def test_list_layout_cmems(
        self,
        l4_ssha_dir_layout_cmems: Path,
        l4_ssha_files: list[str],
        expected: list[int],
        filters: dict[str, tp.Any],
    ):

        collector = FileSystemMetadataCollector(
            l4_ssha_dir_layout_cmems,
            NetcdfFilesDatabaseGriddedSLA.layouts,
            LocalFileSystem(),
        )

        actual = {
            os.path.basename(f) for f in collector.to_dataframe(**filters).filename
        }
        expected = {os.path.basename(l4_ssha_files[ii]) for ii in expected}
        assert len(expected) > 0
        assert expected == actual
