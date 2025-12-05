from __future__ import annotations

import typing as tp

import pytest

if tp.TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="session")
def dac_files() -> list[str]:
    return [
        "dac_dif_26664_12.nc",
        "dac_dif_26666_00.nc",
        "dac_dif_2days_26667_12.nc",
        "dac_dif_40days_26667_18.nc",
    ]


@pytest.fixture(scope="session")
def dac_dir(tmp_path_factory: pytest.TempPathFactory, dac_files: list[str]) -> Path:
    # create test folder
    test_dir = tmp_path_factory.mktemp("test_dir")

    # create test files
    for file in dac_files:
        f = test_dir / file
        f.touch()

    return test_dir
