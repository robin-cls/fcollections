from __future__ import annotations

import typing as tp

import numpy as np
import pytest

from fcollections.implementations import CMEMS_OC_LAYOUT, NetcdfFilesDatabaseOC
from fcollections.implementations._definitions._cmems import DataType, Sensors, Variable

if tp.TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "params, result_size",
    [
        ({}, 4),
        ({"time": np.datetime64("2025-03-03")}, 1),
        ({"type": DataType.NRT}, 1),
        ({"level": "l3"}, 2),
        ({"sensor": Sensors.MULTI}, 2),
        ({"variable": Variable.OPTICS}, 1),
        ({"spatial_resolution": "1km"}, 1),
        ({"temporal_resolution": "P1M"}, 1),
    ],
)
def test_list_chl(chl_dir_flat: Path, params: dict[str, tp.Any], result_size: int):
    db = NetcdfFilesDatabaseOC(chl_dir_flat)

    files = db.list_files(**params)
    assert files["filename"].size == result_size


@pytest.mark.parametrize(
    "params, result_size",
    [
        ({}, 4),
        ({"time": np.datetime64("2025-03-03")}, 1),
        ({"type": DataType.NRT}, 1),
        ({"level": "l3"}, 2),
        ({"sensor": Sensors.MULTI}, 2),
        ({"variable": Variable.OPTICS}, 1),
        ({"spatial_resolution": "1km"}, 1),
        ({"temporal_resolution": "P1M"}, 1),
    ],
)
def test_list_chl_layout(
    chl_dir_layout: Path, params: dict[str, tp.Any], result_size: int
):
    db = NetcdfFilesDatabaseOC(chl_dir_layout)

    files = db.list_files(**params)
    assert files["filename"].size == result_size


def test_query(chl_dir_flat: Path):
    db = NetcdfFilesDatabaseOC(chl_dir_flat)
    ds = db.query()
    assert ds is not None


@pytest.mark.without_geo_packages
def test_query_bbox_disabled(chl_dir: Path):
    db = NetcdfFilesDatabaseOC(chl_dir)
    with pytest.raises(ValueError):
        db.query(bbox=(-180, -90, 180, 90))


@pytest.mark.parametrize(
    "dataset_id",
    [
        # OCEANCOLOUR_GLO_BGC_L3_MY_009_103
        "cmems_obs-oc_glo_bgc-plankton_my_l3-multi-4km_P1D",
        "cmems_obs-oc_glo_bgc-optics_my_l3-multi-4km_P1D",
        "cmems_obs-oc_glo_bgc-plankton_my_l3-olci-300m_P1D",
        "cmems_obs-oc_glo_bgc-plankton_my_l3-olci-4km_P1D",
        "cmems_obs-oc_glo_bgc-reflectance_my_l3-multi-4km_P1D",
        "cmems_obs-oc_glo_bgc-reflectance_my_l3-olci-300m_P1D",
        "cmems_obs-oc_glo_bgc-reflectance_my_l3-olci-4km_P1D",
        "cmems_obs-oc_glo_bgc-transp_my_l3-multi-4km_P1D",
        "cmems_obs-oc_glo_bgc-transp_my_l3-olci-4km_P1D",
        # OCEANCOLOUR_GLO_BGC_L4_MY_009_104
        "cmems_obs-oc_glo_bgc-optics_my_l4-multi-4km_P1M",
        "cmems_obs-oc_glo_bgc-plankton_my_l4-gapfree-multi-4km_P1D",
        "cmems_obs-oc_glo_bgc-plankton_my_l4-multi-4km_P1M",
        "cmems_obs-oc_glo_bgc-plankton_my_l4-multi-climatology-4km_P1D",
        "cmems_obs-oc_glo_bgc-plankton_my_l4-olci-300m_P1M",
        "cmems_obs-oc_glo_bgc-plankton_my_l4-olci-4km_P1M",
        "cmems_obs-oc_glo_bgc-pp_my_l4-multi-4km_P1M",
        "cmems_obs-oc_glo_bgc-reflectance_my_l4-multi-4km_P1M",
        "cmems_obs-oc_glo_bgc-reflectance_my_l4-olci-300m_P1M",
        "cmems_obs-oc_glo_bgc-reflectance_my_l4-olci-4km_P1M",
        "cmems_obs-oc_glo_bgc-transp_my_l4-gapfree-multi-4km_P1D",
        "cmems_obs-oc_glo_bgc-transp_my_l4-multi-4km_P1M",
        "cmems_obs-oc_glo_bgc-transp_my_l4-olci-4km_P1M",
        # OCEANCOLOUR_GLO_BGC_L4_NRT_009_102
        "cmems_obs-oc_glo_bgc-optics_nrt_l4-multi-4km_P1M",
        "cmems_obs-oc_glo_bgc-plankton_nrt_l4-gapfree-multi-4km_P1D",
        "cmems_obs-oc_glo_bgc-plankton_nrt_l4-multi-4km_P1M",
        "cmems_obs-oc_glo_bgc-plankton_nrt_l4-olci-300m_P1M",
        "cmems_obs-oc_glo_bgc-plankton_nrt_l4-olci-4km_P1M",
        "cmems_obs-oc_glo_bgc-pp_nrt_l4-multi-4km_P1M",
        "cmems_obs-oc_glo_bgc-reflectance_nrt_l4-multi-4km_P1M",
        "cmems_obs-oc_glo_bgc-reflectance_nrt_l4-olci-300m_P1M",
        "cmems_obs-oc_glo_bgc-reflectance_nrt_l4-olci-4km_P1M",
        "cmems_obs-oc_glo_bgc-transp_nrt_l4-gapfree-multi-4km_P1D",
        "cmems_obs-oc_glo_bgc-transp_nrt_l4-multi-4km_P1M",
        "cmems_obs-oc_glo_bgc-transp_nrt_l4-olci-4km_P1M",
    ],
)
def test_dataset_id_regex(dataset_id: str):
    """Check dataset id convention building."""
    actual = CMEMS_OC_LAYOUT.conventions[0].match(dataset_id)
    assert actual is not None
