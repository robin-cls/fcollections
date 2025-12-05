from __future__ import annotations

import typing as tp

import pytest

if tp.TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="session")
def swh_files() -> list[str]:
    return [
        "global_vavh_l3_rt_swot_20250310T090000_20250310T120000_20250310T140759.nc",
        "global_vavh_l3_rt_s6a_lr_20250312T000000_20250312T030000_20250312T060604.nc",
        "global_vavh_l3_rt_s6a_lr_20250308T210000_20250309T000000_20250309T030604.nc",
    ]


@pytest.fixture(scope="session")
def swh_dir(tmp_path_factory: pytest.TempPathFactory, swh_files: list[str]) -> Path:
    # create test folder
    test_dir = tmp_path_factory.mktemp("test_dir")

    # create test files
    for file in swh_files:
        f = test_dir / file
        f.touch()

    return test_dir
