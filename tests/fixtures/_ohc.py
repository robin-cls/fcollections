from __future__ import annotations

import typing as tp

import pytest

if tp.TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="session")
def ohc_files() -> list[str]:
    return [
        "OHC-NAQG3_v1r0_blend_s202409130000000_e202409262359599_c202409260921389.nc",
    ]


@pytest.fixture(scope="session")
def ohc_dir(tmp_path_factory: pytest.TempPathFactory, ohc_files: list[str]) -> Path:
    # create test folder
    test_dir = tmp_path_factory.mktemp("test_dir")

    # create test files
    for file in ohc_files:
        f = test_dir / file
        f.touch()

    return test_dir
