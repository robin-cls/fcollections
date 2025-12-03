from __future__ import annotations

import os
import typing as tp

import numpy as np
import pytest

from fcollections.core import FileDiscoverer, FileSystemIterable
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

    convention = FileNameConventionGriddedSLAInternal()

    def test_internal_convention_generate(self):

        reference = "msla_oer_merged_h_27029.nc"
        period = Period(np.datetime64("2024-01-02"), np.datetime64("2024-01-03"))
        actual = self.convention.generate(date=period)
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
        self, l4_ssha_dir: Path, params: dict[str, tp.Any], result_size: int
    ):
        db = NetcdfFilesDatabaseGriddedSLA(l4_ssha_dir)

        files = db.list_files(**params)
        assert files["filename"].size == result_size


class TestQuery:

    def test_bad_kwargs(self, l4_ssha_dir: Path):
        db = NetcdfFilesDatabaseGriddedSLA(l4_ssha_dir)
        with pytest.raises(ValueError):
            db.list_files(bad_arg="bad_arg")
        with pytest.raises(ValueError):
            db.query(bad_arg="bad_arg")

    @pytest.mark.without_geo_packages
    def test_query_bbox_disabled(self, l4_ssha_dir: Path):
        db = NetcdfFilesDatabaseGriddedSLA(l4_ssha_dir)
        with pytest.raises(ValueError):
            db.query(bbox=(-180, -90, 180, 90))


class TestLayout:

    def test_generate_layout(self):
        path = AVISO_L4_SWOT_LAYOUT.generate(
            "/duacs-experimental/dt-phy-grids/l4_karin_nadir",
            method="miost",
            version="1.0",
            phase=MissionsPhases.science,
        )

        assert (
            path == "/duacs-experimental/dt-phy-grids/l4_karin_nadir/v1.0/miost/science"
        )

    @pytest.mark.parametrize(
        "filters, expected",
        [
            ({}, [0, 1, 2, 3]),
            ({"version": "0.3"}, [2, 3]),
            ({"method": "4dvarnet"}, [2]),
            ({"phase": "science"}, [0, 1]),
        ],
    )
    def test_list_layout(
        self,
        l4_ssha_dir_layout: Path,
        l4_ssha_files: list[str],
        expected: list[int],
        filters: dict[str, tp.Any],
    ):

        fd = FileDiscoverer(
            FileNameConventionGriddedSLA(),
            FileSystemIterable(layout=AVISO_L4_SWOT_LAYOUT),
        )

        actual = {
            os.path.basename(f) for f in fd.list(l4_ssha_dir_layout, **filters).filename
        }
        expected = {os.path.basename(l4_ssha_files[ii]) for ii in expected}
        assert len(expected) > 0
        assert expected == actual
