from __future__ import annotations

import typing as tp

import pytest

if tp.TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="session")
def sst_files() -> list[str]:
    return [
        "flat/20231016000000-IFR-L3S_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v02.1-fv01.0.nc",
        "flat/20231030000000-IFR-L3S_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v02.1-fv01.0.nc",
        "layout/cmems_obs-sst_glo_phy_l3s_pir_P1D-m/2023/10/20231016000000-IFR-L3S_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v02.1-fv01.0.nc",
        "layout/cmems_obs-sst_glo_phy_l3s_pir_P1D-m/2023/10/20231030000000-IFR-L3S_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v02.1-fv01.0.nc",
        "layout2/IFREMER-GLOB-SST-L3-NRT-OBS_FULL_TIME_SERIE/2023/10/20231016000000-IFR-L3S_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v02.1-fv01.0.nc",
        "layout2/IFREMER-GLOB-SST-L3-NRT-OBS_FULL_TIME_SERIE/2023/10/20231030000000-IFR-L3S_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v02.1-fv01.0.nc",
    ]


@pytest.fixture(scope="session")
def sst_dir(tmp_path_factory: pytest.TempPathFactory, sst_files: list[str]) -> Path:
    # create test folder
    test_dir = tmp_path_factory.mktemp("test_dir")

    # create test files
    for file in sst_files:
        f = test_dir / file
        f.parent.mkdir(parents=True, exist_ok=True)
        f.touch()

    return test_dir


@pytest.fixture(scope="session")
def sst_dir_flat(sst_dir: Path) -> Path:
    return sst_dir / "flat"


@pytest.fixture(scope="session")
def sst_dir_layout(sst_dir: Path) -> Path:
    return sst_dir / "layout"


@pytest.fixture(scope="session")
def sst_dir_layout2(sst_dir: Path) -> Path:
    return sst_dir / "layout2"
