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


def test_compose_single():
    # This test should protect us against a potential RecursionError
    compose(sum)([2, 3]) == sum([2, 3])


@pytest.fixture
def dataset():
    return xr.Dataset(data_vars=dict(var_1=("dim_0", np.arange(10))))


@pytest.fixture
def files(dataset, tmp_path):
    dataset.to_netcdf(tmp_path / "test.nc")
    memory = fsspec.get_mapper("memory://")
    local = fsspec.get_mapper(f"local://{tmp_path}")
    memory["test1.nc"] = local["test.nc"]
    memory["test2.nc"] = local["test.nc"]
    memory["test3.nc"] = local["test.nc"]
    memory["test4.nc"] = local["test.nc"]
    return [[["test1.nc"], ["test2.nc"]], [["test3.nc"], ["test4.nc"]]]


def test_open_mfdataset_fs(dataset, files):
    options = dict(
        engine="h5netcdf", concat_dim=["dim_1", "dim_2", "dim_3"], combine="nested"
    )
    ds = OpenMfDataset(options).read(files, fs=fs_mem.MemoryFileSystem())
    assert dict(ds.sizes) == {"dim_3": 1, "dim_2": 2, "dim_1": 2, "dim_0": 10}
    assert ds.isel(dim_1=0, dim_2=0, dim_3=0).equals(dataset)


def test_metadata(files):
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
