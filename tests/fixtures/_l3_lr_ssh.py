from __future__ import annotations

import copy
import itertools
import typing as tp
from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from fcollections.core import GroupMetadata, VariableMetadata

from ._generation import (
    HalfOrbitTrackCoordinatesGenerator,
    group_metadata_to_xarray,
)
from ._l2_lr_ssh import _swath_properties

if tp.TYPE_CHECKING:
    import numpy.typing as np_t


@pytest.fixture(scope="session")
def _l3_lr_ssh_basic_metadata() -> GroupMetadata:
    return GroupMetadata(
        name="/",
        variables=[
            VariableMetadata("time", np.dtype("M8[ns]"), ("num_lines",), {}),
            VariableMetadata("longitude", float, ("num_lines", "num_pixels"), {}),
            VariableMetadata("latitude", float, ("num_lines", "num_pixels"), {}),
            VariableMetadata("ssha_noiseless", float, ("num_lines", "num_pixels"), {}),
            VariableMetadata("i_num_line", int, ("num_nadir",), {}),
            VariableMetadata("i_num_pixel", int, ("num_nadir",), {}),
        ],
        dimensions={
            "num_lines": 9860,
            "num_pixels": 69,
            "num_nadir": int(np.ceil(9860 / 3)),
        },
        attributes={},
        subgroups=[],
    )


class BasicGenerator(HalfOrbitTrackCoordinatesGenerator):

    def ssha_noiseless(self, shape: tuple[int, ...]) -> np_t.NDArray[np.float64]:
        return self._random_generator.random(shape)

    def i_num_line(self, shape: tuple[int]) -> np_t.NDArray[np.int64]:
        return np.arange(0, 3 * shape[0], 3)

    def i_num_pixel(self, shape: tuple[int]) -> np_t.NDArray[np.int64]:
        return np.full(shape[0], fill_value=34)


@pytest.fixture(scope="session")
def l3_lr_ssh_basic_dataset(_l3_lr_ssh_basic_metadata: GroupMetadata) -> xr.Dataset:
    generator = BasicGenerator(
        *_swath_properties(25),
        t0=np.datetime64("2024-01-01T11:39"),
        dt=np.timedelta64(100, "ms"),
    )

    ds = group_metadata_to_xarray(_l3_lr_ssh_basic_metadata, generator)

    return ds.set_coords(["time", "longitude", "latitude"])


@pytest.fixture(scope="session")
def _l3_lr_ssh_expert_metadata(
    _l3_lr_ssh_basic_metadata: GroupMetadata,
) -> GroupMetadata:
    metadata = copy.deepcopy(_l3_lr_ssh_basic_metadata)
    metadata.variables.extend(
        [VariableMetadata("cross_track_distance", float, ("num_pixels",), {})]
    )
    return metadata


class ExpertGenerator(BasicGenerator):

    def cross_track_distance(self, shape: tuple[int]) -> np_t.NDArray[np.float64]:
        return np.arange(-(shape[0] - 1) * 1000, shape[0] * 1000 + 1, 2000).astype(
            float
        )


@pytest.fixture(scope="session")
def l3_lr_ssh_expert_dataset(_l3_lr_ssh_expert_metadata: GroupMetadata) -> xr.Dataset:
    generator = ExpertGenerator(
        *_swath_properties(25),
        t0=np.datetime64("2024-01-01T11:39"),
        dt=np.timedelta64(100, "ms"),
    )

    ds = group_metadata_to_xarray(_l3_lr_ssh_expert_metadata, generator)

    return ds.set_coords(["time", "longitude", "latitude"])


@pytest.fixture(scope="session")
def l3_lr_ssh_unsmoothed_dataset(
    _l3_lr_ssh_expert_metadata: GroupMetadata,
) -> xr.Dataset:
    generator = ExpertGenerator(
        *_swath_properties(25),
        t0=np.datetime64("2024-01-01T11:39"),
        dt=np.timedelta64(100, "ms"),
        half_orbit_numbers=iter([(10, 532)]),
    )

    ds = group_metadata_to_xarray(_l3_lr_ssh_expert_metadata, generator)
    return ds.drop_dims(["num_nadir"]).set_coords(["time", "longitude", "latitude"])


@pytest.fixture(scope="session")
def half_orbit_map(
    _l3_lr_ssh_basic_metadata: xr.Dataset,
) -> dict[tuple[int, int], xr.Dataset]:
    # Use the basic dataset and bump the time to build multiple mock data. Note
    # that the time of the basic dataset has been chosen so that the (4, 501)
    # half orbit is between two partitions
    _half_orbit_map = {}
    metadata = copy.deepcopy(_l3_lr_ssh_basic_metadata)
    metadata.variables.extend(
        [
            VariableMetadata("cycle_number", int, ("num_lines",), {}),
            VariableMetadata("pass_number", int, ("num_lines",), {}),
        ]
    )

    generator = BasicGenerator(
        *_swath_properties(25),
        # t0=np.datetime64('2024-01-01T11:39'),
        t0=np.datetime64("2024-01-01T13:54"),
        dt=np.timedelta64(100, "ms"),
        half_orbit_numbers=filter(
            lambda x: x not in [(2, 500), (3, 502)],
            itertools.product(range(1, 6), range(500, 503)),
        ),
    )

    for _ in generator:
        ds = group_metadata_to_xarray(metadata, generator)
        half_orbit = generator.half_orbit_number
        if half_orbit == (1, 501):
            ds = ds.isel(num_lines=slice(1, None))

        _half_orbit_map[half_orbit] = ds

    return _half_orbit_map


@pytest.fixture(scope="session")
def l3_lr_ssh_files() -> list[str]:
    # The files that we will use to test the listing
    return [
        "v1_0_2/Basic/cycle_531/SWOT_L3_LR_SSH_Basic_531_025_20230310T051804_20230310T060909_v1.0.2.nc",
        "v1_0_2/Basic/cycle_531/SWOT_L3_LR_SSH_Basic_531_026_20230310T060910_20230310T070014_v1.0.2.nc",
        "v1_0_2/Basic/cycle_532/SWOT_L3_LR_SSH_Basic_532_025_20230406T051804_20230406T060909_v1.0.2.nc",
        "v1_0_2/Basic/cycle_532/SWOT_L3_LR_SSH_Basic_532_026_20230406T060910_20230406T070014_v1.0.2.nc",
        "v1_0_2/Expert/reproc/cycle_532/SWOT_L3_LR_SSH_Expert_532_025_20230406T051804_20230406T060909_v1.0.2.nc",
        "v2_0_1/Expert/reproc/cycle_532/SWOT_L3_LR_SSH_Expert_532_025_20230406T051804_20230406T060909_v2.0.1.nc",
        "v2_0_1/Expert/reproc/cycle_532/SWOT_L3_LR_SSH_Expert_532_026_20230406T051804_20230406T060909_v2.0.1.nc",
        "v2_0_1/Expert/reproc/cycle_533/SWOT_L3_LR_SSH_Expert_533_025_20230407T051804_20230407T060909_v2.0.1.nc",
        "v2_0_1/Expert/reproc/cycle_533/SWOT_L3_LR_SSH_Expert_533_026_20230407T051804_20230407T060909_v2.0.1.nc",
        "v2_0_1/Unsmoothed/forward/cycle_010/SWOT_L3_LR_SSH_Unsmoothed_010_532_20240125T025352_20240125T034438_v2.0.1.nc",
    ]


@pytest.fixture(scope="session")
def l3_lr_ssh_dir_empty_files(
    tmp_path_factory: pytest.TempPathFactory, l3_lr_ssh_files: list[str]
) -> Path:
    root = tmp_path_factory.mktemp("l3_lr_ssh")

    # create test folder
    for filepath in l3_lr_ssh_files:
        filepath = root / Path(filepath).name

        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.touch()

    return root


@pytest.fixture(scope="session")
def l3_lr_ssh_dir_empty_files_layout(
    tmp_path_factory: pytest.TempPathFactory, l3_lr_ssh_files: list[str]
) -> Path:
    root = tmp_path_factory.mktemp("l3_lr_ssh")

    # create test folder
    for filepath in l3_lr_ssh_files:
        filepath = root / filepath

        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.touch()

    return root


@pytest.fixture(scope="session")
def l3_lr_ssh_dir(
    tmpdir_factory: pytest.TempdirFactory,
    _l3_lr_ssh_basic_metadata: GroupMetadata,
    _l3_lr_ssh_expert_metadata: GroupMetadata,
    l3_lr_ssh_files: list[str],
) -> Path:
    # Initiate the generators. These generators should be the same as the
    # 'datasets' fixtures
    basic_generator = BasicGenerator(
        *_swath_properties(25),
        t0=np.datetime64("2024-01-01T11:39"),
        dt=np.timedelta64(100, "ms"),
        half_orbit_numbers=itertools.product([531, 532], [25, 26]),
    )

    expert_generator = ExpertGenerator(
        *_swath_properties(25),
        t0=np.datetime64("2024-01-01T11:39"),
        dt=np.timedelta64(100, "ms"),
        half_orbit_numbers=iter([(532, 25), *itertools.product([532, 533], [25, 26])]),
    )

    unsmoothed_generator = ExpertGenerator(
        *_swath_properties(25),
        t0=np.datetime64("2024-01-01T11:39"),
        dt=np.timedelta64(100, "ms"),
        half_orbit_numbers=iter([(10, 532)]),
    )

    # Create fake data for the netcdf files, do not just use touch() to simulate
    # the file tree
    root_dir = Path(tmpdir_factory.mktemp("l3_lr_ssh"))
    for file, _ in zip(l3_lr_ssh_files[:4], basic_generator, strict=True):
        relative_path = Path(file)
        path = root_dir / "basic" / relative_path.name
        path.parent.mkdir(parents=True, exist_ok=True)
        basic_dataset = group_metadata_to_xarray(
            _l3_lr_ssh_basic_metadata, basic_generator
        )
        basic_dataset.to_netcdf(path)

    for file, _ in zip(l3_lr_ssh_files[4:9], expert_generator, strict=True):
        relative_path = Path(file)
        path = root_dir / "expert" / relative_path.name
        path.parent.mkdir(parents=True, exist_ok=True)
        expert_dataset = group_metadata_to_xarray(
            _l3_lr_ssh_expert_metadata, expert_generator
        )
        expert_dataset.to_netcdf(path)

    for file, _ in zip(l3_lr_ssh_files[9:], unsmoothed_generator, strict=True):
        relative_path = Path(file)
        path = root_dir / "unsmoothed" / relative_path.name
        path.parent.mkdir(parents=True, exist_ok=True)
        unsmoothed_dataset = group_metadata_to_xarray(
            _l3_lr_ssh_expert_metadata, unsmoothed_generator
        )
        unsmoothed_dataset.drop_dims(["num_nadir"]).to_netcdf(path)

    return root_dir


@pytest.fixture(scope="session")
def l3_lr_ssh_basic_dir(l3_lr_ssh_dir: Path) -> Path:
    return l3_lr_ssh_dir / "basic"


@pytest.fixture(scope="session")
def l3_lr_ssh_expert_dir(l3_lr_ssh_dir: Path) -> Path:
    return l3_lr_ssh_dir / "expert"


@pytest.fixture(scope="session")
def l3_lr_ssh_unsmoothed_dir(l3_lr_ssh_dir: Path) -> Path:
    return l3_lr_ssh_dir / "unsmoothed"


@pytest.fixture(scope="session")
def l3_lr_ssh_basic_files(l3_lr_ssh_basic_dir: Path) -> list[Path]:
    return sorted(l3_lr_ssh_basic_dir.iterdir())


@pytest.fixture(scope="session")
def l3_lr_ssh_expert_files(l3_lr_ssh_expert_dir: Path) -> list[Path]:
    return sorted(l3_lr_ssh_expert_dir.iterdir())


@pytest.fixture(scope="session")
def l3_lr_ssh_unsmoothed_files(l3_lr_ssh_unsmoothed_dir: Path) -> list[Path]:
    return sorted(l3_lr_ssh_unsmoothed_dir.iterdir())


@pytest.fixture(scope="session")
def l3_lr_ssh_basic_files_unique(l3_lr_ssh_basic_files: list[Path]) -> list[list[Path]]:
    return l3_lr_ssh_basic_files


@pytest.fixture(scope="session")
def l3_lr_ssh_expert_files_unique(
    l3_lr_ssh_expert_files: list[Path],
) -> list[list[Path]]:
    return l3_lr_ssh_expert_files[1:]
