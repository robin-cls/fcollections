from __future__ import annotations

import typing as tp

import pytest

if tp.TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="session")
def mur_files() -> list[str]:
    return [
        "20250309090000-JPL-L4_GHRSST-SSTfnd-MUR-GLOB-v02.0-fv04.1.nc",
        "20250305090000-JPL-L4_GHRSST-SSTfnd-MUR-GLOB-v02.0-fv04.1.nc",
    ]


@pytest.fixture(scope="session")
def mur_dir(tmp_path_factory: pytest.TempPathFactory, mur_files: list[str]) -> Path:
    # create test folder
    test_dir = tmp_path_factory.mktemp("test_dir")

    # create test files
    for file in mur_files:
        f = test_dir / file
        f.touch()

    return test_dir
