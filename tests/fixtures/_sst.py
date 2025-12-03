from __future__ import annotations

import typing as tp

import pytest

if tp.TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="session")
def sst_files() -> list[str]:
    return [
        "20231016000000-IFR-L3S_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v02.1-fv01.0.nc",
        "20231030000000-IFR-L3S_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v02.1-fv01.0.nc",
    ]


@pytest.fixture(scope="session")
def sst_dir(tmp_path_factory: pytest.TempPathFactory, sst_files: list[str]) -> Path:
    # create test folder
    test_dir = tmp_path_factory.mktemp("test_dir")

    # create test files
    for file in sst_files:
        f = test_dir / file
        f.touch()

    return test_dir
