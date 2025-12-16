import typing as tp
from pathlib import Path

import numpy as np
import pytest

from fcollections.implementations import (
    NetcdfFilesDatabaseL2Nadir,
)


def test_bad_kwargs(l2_nadir_dir: Path):
    db = NetcdfFilesDatabaseL2Nadir(l2_nadir_dir)
    with pytest.raises(ValueError):
        db.list_files(bad_arg="bad_arg")
    with pytest.raises(ValueError):
        db.query(bad_arg="bad_arg")


@pytest.mark.parametrize(
    "args, result_size",
    [
        ({}, 3),
        ({"time": (np.datetime64("2023-07-07"), np.datetime64("2023-07-08"))}, 2),
        ({"cycle_number": 575}, 2),
        ({"pass_number": 14}, 2),
        ({"cycle_number": 574, "pass_number": 15}, 0),
    ],
)
def test_list_l2_nadir(l2_nadir_dir: Path, args: dict[str, tp.Any], result_size: int):

    db = NetcdfFilesDatabaseL2Nadir(l2_nadir_dir)

    files = db.list_files(**args)
    assert files["filename"].size == result_size
