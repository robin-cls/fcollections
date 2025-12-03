from __future__ import annotations

import typing as tp
from pathlib import Path

import pytest

if tp.TYPE_CHECKING:
    import xarray as xr_t


@pytest.fixture(scope="session")
def chl_files() -> list[str]:
    return [
        "20250302_cmems_obs-oc_glo_bgc-plankton_nrt_l3-multi-4km_P1D.nc",
        "20250302_cmems_obs-oc_glo_bgc-plankton_myint_l3-olci-4km_P1D.nc",
        "20250302_cmems_obs-oc_glo_bgc-optics_myint_l4-olci-1km_P1D.nc",
        "20250303_cmems_obs-oc_glo_bgc-plankton_myint_l4-gapfree-multi-4km_P1M.nc",
    ]


@pytest.fixture(scope="session")
def chl_dir(
    l4_ssha_dataset_0_360: xr_t.Dataset,
    tmpdir_factory: pytest.TempdirFactory,
    chl_files: list[str],
) -> Path:
    """The test folder will contain multiple netcdf."""
    data_dir = Path(tmpdir_factory.mktemp("data"))

    test_dir = data_dir.joinpath("test_dir")
    test_dir.mkdir(exist_ok=True)

    for f in chl_files:
        l4_ssha_dataset_0_360.to_netcdf(test_dir.joinpath(f))

    return test_dir
