from __future__ import annotations

import typing as tp

import pytest

if tp.TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="session")
def era5_files() -> list[str]:
    return [
        "reanalysis-era5-single-levels_20250302.nc",
        "reanalysis-era5-single-levels_20250303.nc",
    ]


@pytest.fixture(scope="session")
def era5_dir(tmp_path_factory: pytest.TempPathFactory, era5_files: list[str]) -> Path:
    # create test folder
    test_dir = tmp_path_factory.mktemp("test_dir")

    # create test files
    for file in era5_files:
        f = test_dir / file
        f.touch()

    return test_dir
