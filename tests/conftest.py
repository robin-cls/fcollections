import sys
from pathlib import Path

import pytest
from fixtures._auto import patch_test_geometries_path
from fixtures._chl import chl_dir, chl_files
from fixtures._dac import dac_dir, dac_files
from fixtures._era5 import era5_dir, era5_files
from fixtures._l2_lr_ssh import (
    _l2_lr_ssh_basic_metadata,
    _l2_lr_ssh_expert_metadata,
    l2_lr_ssh_basic_dataset,
    l2_lr_ssh_basic_dir,
    l2_lr_ssh_basic_files,
    l2_lr_ssh_basic_files_unique,
    l2_lr_ssh_dir,
    l2_lr_ssh_dir_empty_files,
    l2_lr_ssh_dir_empty_files_layout,
    l2_lr_ssh_expert_dataset,
    l2_lr_ssh_expert_dir,
    l2_lr_ssh_expert_files,
    l2_lr_ssh_expert_files_unique,
    l2_lr_ssh_files,
    l2_lr_ssh_unsmoothed_dataset,
    l2_lr_ssh_unsmoothed_dir,
    l2_lr_ssh_unsmoothed_files,
)
from fixtures._l3_lr_ssh import (
    _l3_lr_ssh_basic_metadata,
    _l3_lr_ssh_expert_metadata,
    half_orbit_map,
    l3_lr_ssh_basic_dataset,
    l3_lr_ssh_basic_dir,
    l3_lr_ssh_basic_files,
    l3_lr_ssh_basic_files_unique,
    l3_lr_ssh_dir,
    l3_lr_ssh_dir_empty_files,
    l3_lr_ssh_dir_empty_files_layout,
    l3_lr_ssh_expert_dataset,
    l3_lr_ssh_expert_dir,
    l3_lr_ssh_expert_files,
    l3_lr_ssh_expert_files_unique,
    l3_lr_ssh_files,
    l3_lr_ssh_unsmoothed_dataset,
    l3_lr_ssh_unsmoothed_dir,
    l3_lr_ssh_unsmoothed_files,
)
from fixtures._l4_ssha import (
    l4_ssha_dataset_0_360,
    l4_ssha_dataset_180_180,
    l4_ssha_dataset_reversed_lat,
    l4_ssha_dir,
    l4_ssha_dir_layout,
    l4_ssha_files,
    l4_ssha_files_2,
)
from fixtures._mur import mur_dir, mur_files
from fixtures._nadir import (
    l2_nadir_dir,
    l2_nadir_files,
    l3_nadir_dataset_0_360,
    l3_nadir_dataset_180_180,
    l3_nadir_dir,
    l3_nadir_dir_layout,
    l3_nadir_files,
    l3_nadir_files_2,
)
from fixtures._ohc import ohc_dir, ohc_files
from fixtures._s1aowi import s1aowi_dir, s1aowi_files
from fixtures._sst import sst_dir, sst_files
from fixtures._swh import swh_dir, swh_files
from fixtures._ww import (
    _extended_metadata,
    _light_metadata,
    l3_lr_ww_dir_layout,
    l3_lr_ww_extended_dataset,
    l3_lr_ww_extended_files,
    l3_lr_ww_files,
    l3_lr_ww_light_dataset,
    l3_lr_ww_light_files,
)


@pytest.fixture(scope="session")
def resources_directory():
    return Path(__file__).parent / "resources"


def pytest_sessionstart(session: pytest.Session):
    """Simulate missing optional dependencies before test collection starts.

    Simulate an ImportError in the optional package. A more realistic
    case would be to simulate pyinterp, geopandas and shapely missing,
    but these packages are required in the fixtures generation, so we
    must simulate the error at a higher level.
    """
    if session.config.getoption("--without-geo-packages"):
        sys.modules["fcollections.implementations.optional"] = None


def pytest_addoption(parser: pytest.Parser):
    """Add an option to run the tests without the geo packages."""
    parser.addoption(
        "--without-geo-packages",
        action="store_true",
        default=False,
        help="Simulate missing geo packages like 'pyinterp', 'shapely' and 'geopandas'",
    )


def pytest_configure(config: pytest.Config):
    config.addinivalue_line(
        "markers", "with_geo_packages: tests that need geo packages to run"
    )
    config.addinivalue_line(
        "markers",
        "without_geo_packages: tests that should be run with missing geo packages",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):
    """Filter out tests that needs missing/present geo packages."""
    simulate_missing = config.getoption("--without-geo-packages")

    keyword = "with_geo_packages" if simulate_missing else "without_geo_packages"

    # Filter to only tests marked with @pytest.mark.optional
    kept = []
    deselected = []
    for item in items:
        if keyword in item.keywords:
            deselected.append(item)
        else:
            kept.append(item)
    items[:] = kept
    config.hook.pytest_deselected(items=deselected)


@pytest.fixture(autouse=True, scope="session")
def xarray_future_defaults():
    import xarray as xr

    xr.set_options(use_new_combine_kwarg_defaults=True)
