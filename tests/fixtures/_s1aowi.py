from __future__ import annotations

import typing as tp

import pytest

if tp.TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="session")
def s1aowi_files() -> list[str]:
    return [
        "s1a-iw-owi-cm-20240924t111921-20240924t112018-000003-055806_gs.nc",
        "s1a-iw-owi-ocn-20240924t112142-20240924t112211-000003-055807_sw.nc",
    ]


@pytest.fixture(scope="session")
def s1aowi_dir(
    tmp_path_factory: pytest.TempPathFactory, s1aowi_files: list[str]
) -> Path:
    # create test folder
    test_dir = tmp_path_factory.mktemp("test_dir")

    # create test files
    for file in s1aowi_files:
        f = test_dir / file
        f.touch()

    return test_dir
