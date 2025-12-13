from __future__ import annotations

import typing as tp

import fsspec
import fsspec.implementations.memory as fs_mem
import numpy as np
import pytest
import xarray as xr

from fcollections.core import (
    GroupMetadata,
    OpenMfDataset,
    VariableMetadata,
    compose,
)

if tp.TYPE_CHECKING:
    from pathlib import Path


def test_compose_single():
    # This test should protect us against a potential RecursionError
    compose(sum)([2, 3]) == sum([2, 3])


def test_compose_multiple():
    new_func = compose(sum, lambda x: x + 1, lambda x: [x, x**2])
    assert new_func([2, 3]) == [6, 36]


@pytest.fixture(scope="session")
def dataset() -> xr.Dataset:
    return xr.Dataset(data_vars=dict(var_1=("dim_0", np.arange(10))))


@pytest.fixture(scope="session")
def local_folder(dataset: xr.Dataset, tmp_path_factory: pytest.TempPathFactory) -> Path:
    tmp_path = tmp_path_factory.mktemp("local_folder")
    dataset.to_netcdf(tmp_path / "test.nc")
    return tmp_path


@pytest.fixture(scope="session")
def files(local_folder: Path) -> list[list[str]]:
    memory = fsspec.get_mapper("memory://")
    local = fsspec.get_mapper(f"local://{local_folder}")
    memory["test1.nc"] = local["test.nc"]
    memory["test2.nc"] = local["test.nc"]
    memory["test3.nc"] = local["test.nc"]
    memory["test4.nc"] = local["test.nc"]
    return [[["test1.nc"], ["test2.nc"]], [["test3.nc"], ["test4.nc"]]]


def test_open_mfdataset_fs(dataset: xr.Dataset, files: list[list[str]]):
    options = dict(
        engine="h5netcdf", concat_dim=["dim_1", "dim_2", "dim_3"], combine="nested"
    )
    ds = OpenMfDataset(options).read(files, fs=fs_mem.MemoryFileSystem())
    assert dict(ds.sizes) == {"dim_3": 1, "dim_2": 2, "dim_1": 2, "dim_0": 10}
    assert ds.isel(dim_1=0, dim_2=0, dim_3=0).equals(dataset)


def test_open_mfdataset_local(dataset: xr.Dataset, local_folder: Path):
    reader = OpenMfDataset({"engine": "h5netcdf"})
    ds = reader.read(sorted(local_folder.iterdir()))
    xr.testing.assert_identical(ds, dataset)


def test_open_mfdataset_no_files():
    reader = OpenMfDataset({"engine": "h5netcdf"})
    with pytest.raises(OSError):
        # xarray exception should be raised
        reader.read([], selected_variables=["var1"])


def test_metadata(files: list[list[str]]):
    metadata = OpenMfDataset().metadata(files[0][0][0], fs=fs_mem.MemoryFileSystem())
    expected = GroupMetadata(
        name="/",
        attributes={},
        dimensions={"dim_0": 10},
        variables=[
            VariableMetadata("var_1", int, ("dim_0",), {}),
        ],
        subgroups=[],
    )
    assert metadata == expected
