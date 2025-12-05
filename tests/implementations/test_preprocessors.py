from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

from fcollections.implementations._readers import (
    _add_cycle_pass_numbers,
    _drop_nadir_dimension,
    _extract_nadir,
    _unclip_nadir,
)


def test_preprocessor_cycle_pass_error_missing_source():
    ds = xr.Dataset()
    with pytest.raises(ValueError, match="source"):
        _add_cycle_pass_numbers(ds)


def test_preprocessor_cycle_pass_error_bad_filename():
    ds = xr.Dataset()
    ds.encoding["source"] = "L2_LR_SSH_Basic_20230608T191826_20230608T200933_PIB0_01.nc"
    with pytest.raises(ValueError, match="pattern"):
        _add_cycle_pass_numbers(ds)


def test_preprocessor_cycle_pass_error_missing_dimension():
    ds = xr.Dataset()
    ds.encoding["source"] = (
        "SWOT_L2_LR_SSH_Basic_546_011_20230608T191826_20230608T200933_PIB0_01.nc"
    )
    with pytest.raises(ValueError, match="num_lines"):
        _add_cycle_pass_numbers(ds)


@pytest.mark.parametrize(
    "filename",
    [
        "SWOT_L2_LR_SSH_Basic_546_011_20230608T191826_20230608T200933_PIB0_01.nc",
        "SWOT_L2_LR_SSH_Expert_546_011_20230608T191826_20230608T200933_PIB0_01.nc",
        "SWOT_L2_LR_SSH_Unsmoothed_546_011_20230608T191826_20230608T200933_PIB0_01.nc",
        "SWOT_L3_LR_SSH_Basic_546_011_20230608T191826_20230608T200933_v0.2.nc",
        "SWOT_L3_LR_SSH_Expert_546_011_20230608T191826_20230608T200933_v0.2.nc",
        "SWOT_L3_LR_SSH_Unsmoothed_546_011_20230608T191826_20230608T200933_v0.2.nc",
    ],
)
def test_preprocessor_cycle_pass(filename: str):
    ds = xr.Dataset(
        data_vars=dict(ssha=(("num_lines", "num_pixels"), np.ones((10, 3))))
    )
    ds.encoding["source"] = filename
    ds = _add_cycle_pass_numbers(ds)
    assert len(ds["cycle_number"]) == len(ds["num_lines"])
    assert len(ds["pass_number"]) == len(ds["num_lines"])
    assert all(ds["cycle_number"] == 546)
    assert all(ds["pass_number"] == 11)


def test_preprocessor_cycle_pass_no_repeat():
    ds = xr.Dataset(
        data_vars=dict(ssha=(("num_lines", "num_pixels"), np.ones((10, 3))))
    )
    ds.encoding["source"] = (
        "SWOT_L2_LR_SSH_Basic_546_011_20230608T191826_20230608T200933_PIB0_01.nc"
    )
    ds = _add_cycle_pass_numbers(
        ds, cycle_number_dimension=None, pass_number_dimension=None
    )
    assert ds["cycle_number"] == 546
    assert ds["pass_number"] == 11


def test_preprocessor_drop_nadir():
    ds = xr.Dataset(
        data_vars={
            "sla": (("num_lines", "num_pixels"), np.ones((30, 4))),
            "i_num_line": ("num_nadir", np.arange(0, 30, 3)),
        }
    )
    assert "num_nadir" in ds.sizes
    preprocessed = _drop_nadir_dimension(ds)
    assert "num_nadir" not in preprocessed


def test_preprocessor_drop_nadir_no_num_nadir():
    ds = xr.Dataset(
        data_vars={
            "sla": (("num_lines", "num_pixels"), np.ones((30, 4))),
        }
    )
    assert "num_nadir" not in ds.sizes
    preprocessed = _drop_nadir_dimension(ds)
    xr.testing.assert_equal(ds, preprocessed)


def test_preprocessor_extract_nadir():
    ds = xr.Dataset(
        data_vars={
            "sla": (("num_lines", "num_pixels"), np.random.random((30, 4))),
            "i_num_line": ("num_nadir", np.arange(0, 30, 3)),
            "i_num_pixel": ("num_nadir", np.repeat(2, 10)),
        }
    )
    reference = ds.sla.values[::3, 2]
    actual = _extract_nadir(ds).sla.values
    assert np.array_equal(reference, actual)


def test_preprocessor_extract_nadir_bad_dataset():
    ds = xr.Dataset(
        data_vars={
            # 'sla': (('num_lines', 'num_pixels'), np.ones((30, 4))),
            "i_num_line": ("num_nadir", np.arange(0, 30, 3)),
            "i_num_pixel": ("num_nadir", np.repeat(2, 10)),
        }
    )
    with pytest.warns(UserWarning):
        actual = _extract_nadir(ds)
    assert actual is None


@pytest.mark.parametrize(
    "variables_to_remove",
    [
        ["i_num_line", "i_num_pixel"],
        ["i_num_line"],
        ["i_num_line"],
    ],
)
def test_preprocessor_extract_nadir_missing_indexes(variables_to_remove: list[str]):
    ds = xr.Dataset(
        data_vars={
            "sla": (("num_lines", "num_pixels"), np.random.random((30, 4))),
            "i_num_line": ("num_nadir", np.arange(0, 30, 3)),
            "i_num_pixel": ("num_nadir", np.repeat(2, 10)),
        }
    ).drop_vars(variables_to_remove)
    actual = _extract_nadir(ds)
    assert actual is None


def test_preprocessor_unclip_nadir():
    ds = xr.Dataset(
        data_vars={
            "sla": (("num_lines", "num_pixels"), np.random.random((30, 4))),
            "sla_noiseless": (("num_lines", "num_pixels"), np.random.random((30, 4))),
            "i_num_line": ("num_nadir", np.arange(0, 30, 3)),
            "i_num_pixel": ("num_nadir", np.repeat(2, 10)),
        }
    )
    actual = _unclip_nadir(ds, {"sla"})
    assert np.all(np.isnan(actual.sla[::3, 2]))
    assert np.isnan(actual.sla[::3, 2]).sum() == np.isnan(actual.sla).sum()
    assert not np.any(np.isnan(actual["sla_noiseless"]))


@pytest.mark.parametrize(
    "variables_to_remove",
    [
        ["i_num_line", "i_num_pixel"],
        ["i_num_line"],
        ["i_num_line"],
    ],
)
def test_preprocessor_unclip_nadir_missing_indexes(variables_to_remove: list[str]):
    ds = xr.Dataset(
        data_vars={
            "sla": (("num_lines", "num_pixels"), np.random.random((30, 4))),
            "i_num_line": ("num_nadir", np.arange(0, 30, 3)),
            "i_num_pixel": ("num_nadir", np.repeat(2, 10)),
        }
    ).drop_vars(variables_to_remove)
    actual = _unclip_nadir(ds, {"sla"})
    xr.testing.assert_equal(ds, actual)


def test_preprocessor_unclip_nadir_missing_indexes():
    ds = xr.Dataset(
        data_vars={
            "sla": (("num_lines", "num_pixels"), np.random.random((30, 4))),
            "i_num_line": ("num_nadir", np.arange(0, 30, 3)),
            "i_num_pixel": ("num_nadir", np.repeat(2, 10)),
        }
    )
    actual = _unclip_nadir(ds, set())
    xr.testing.assert_equal(ds, actual)
