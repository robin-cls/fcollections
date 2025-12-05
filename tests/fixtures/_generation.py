from __future__ import annotations

import dataclasses as dc
import functools
import typing as tp
from copy import copy, deepcopy

import netCDF4 as nc4
import numpy as np
import xarray as xr

from fcollections.core import GroupMetadata, VariableMetadata

if tp.TYPE_CHECKING:
    import numpy.typing as np_t


def group_metadata_to_netcdf(
    nds: nc4.Dataset | nc4.Group,
    group: GroupMetadata,
    generators: dict[str, tp.Callable[[tuple[int, ...]], np_t.NDArray[np.float64]]],
):
    for name, value in group.attributes.items():
        nds.setncattr(name, value)

    for name, size in group.dimensions.items():
        nds.createDimension(name, size)

    dimensions = nds.dimensions
    if nds.parent is not None:
        dimensions |= nds.parent.dimensions

    for variable in group.variables:
        attributes = copy(variable.attributes)
        fill_value = attributes.pop("_FillValue")
        var = nds.createVariable(
            variable.name, variable.dtype, variable.dimensions, fill_value=fill_value
        )

        shape = [dimensions[d].size for d in variable.dimensions]
        values = generators[variable.name](shape)
        if np.issubdtype(values.dtype, np.dtype("M8")):
            values = xr.coding.times.encode_cf_datetime(
                values,
                variable.attributes["units"],
                variable.attributes["calendar"],
                dtype=variable.dtype,
            )[0]
        var[...] = values

        for name, value in attributes.items():
            var.setncattr(name, value)

    for subgroup in group.subgroups:
        ngrp = nds.createGroup(subgroup.name)
        group_metadata_to_netcdf(ngrp, subgroup, generators)


def variable_metadata_to_xarray(
    variable_metadata: VariableMetadata, values: np_t.NDArray[np.float64]
):
    da = xr.DataArray(
        values,
        dims=variable_metadata.dimensions,
        attrs=variable_metadata.attributes,
        name=variable_metadata.name,
    )
    return da


def group_metadata_to_xarray(
    group: GroupMetadata,
    generators: dict[str, tp.Callable[[tuple[int, ...]], np_t.NDArray[np.float64]]],
) -> xr.Dataset:
    dims = group.dimensions

    variables = {}
    for v in group.variables:
        shape = [dims[d] for d in v.dimensions]
        values = generators[v.name](shape)
        variables[v.name] = variable_metadata_to_xarray(v, values)

    return xr.Dataset(
        data_vars=variables,
        attrs=group.attributes,
    )


def pluck(metadata: GroupMetadata, path: str) -> GroupMetadata:

    attributes = {}
    dimensions = {}
    names = []
    variables = []
    for node in metadata.nodes(path):
        names.append(node.name)
        variables.extend(node.variables)
        attributes |= node.attributes
        dimensions |= node.dimensions

    node = deepcopy(node)
    node.name = "/".join(names).lstrip("/")
    node.variables = variables
    node.subgroups = []
    node.dimensions = dimensions
    node.attributes = attributes

    return node


def _default_half_orbit_number_generator() -> (
    tp.Generator[tuple[int, int, int], None, None]
):
    cycle_number, pass_number = 1, 1
    while True:
        yield (cycle_number, pass_number)
        pass_number += 1


@dc.dataclass
class HalfOrbitTrackCoordinatesGenerator:
    # Generate half orbit coordinates with a simple mathematical functions. The
    # epsilon_lon and epsilon_lat are factors of the functions that have been
    # tuned so that the functions are close to a real half orbit ground track
    lon0: float = 60.0
    dlon: float = 160
    lat0: float = 78.0
    t0: np.datetime64 = np.datetime64("2024-01-01")
    dt: np.timedelta64 = np.timedelta64(300, "ms")

    # Swot cycle is around 21 days
    dt_cycle: np.datetime64 = np.timedelta64(int(20.8 * 86400), "s")
    half_orbit_numbers: tp.Iterable[tuple[int, int]] = dc.field(
        default_factory=_default_half_orbit_number_generator
    )

    # Factor for the coordinates approximation function
    epsilon_lon: float = 0.18
    epsilon_lat: float = 0.4

    # To ensure that multiple instances of Generator will give the same result,
    # the random generator will set a fixed seed that will make the random()
    # call predictable
    _random_generator: np.random.Generator = dc.field(init=False)
    _cycle_number: int = dc.field(init=False)
    _pass_number: int = dc.field(init=False)
    _dt_pass: np.timedelta64 | None = dc.field(init=False)
    _t1: np.datetime64 | None = dc.field(init=False)

    def __post_init__(self):
        self._dt_pass = None
        self._t1 = None
        self._cycle_number, self._pass_number = next(self.half_orbit_numbers)
        self._random_generator = np.random.default_rng(12345)

    def __iter__(self):
        return self

    def __next__(self):
        # First iter
        if self._dt_pass is None:
            return

        old_half_orbit_number = self.half_orbit_number
        self._cycle_number, self._pass_number = next(self.half_orbit_numbers)

        bump_cycle = self._cycle_number - old_half_orbit_number[0]
        bump_pass = self._pass_number - old_half_orbit_number[1]
        self.t0 += bump_cycle * self.dt_cycle + bump_pass * self._dt_pass

        self.lon0 += bump_pass * self.dlon
        self.lon0 %= 360
        self.lat0 *= 1 if bump_pass % 2 == 0 else -1

    @property
    def half_orbit_number(self) -> tuple[int, int]:
        return self._cycle_number, self._pass_number

    def time(self, shape: tuple[int, ...]) -> np_t.NDArray[np.datetime64]:
        times = np.arange(self.t0, self.t0 + self.dt * shape[0], self.dt).astype(
            "M8[ns]"
        )
        self._t1 = times[-1]
        self._dt_pass = self._t1 - self.t0
        return times

    def longitude(self, shape: tuple[int, ...]) -> np_t.NDArray[np.float64]:
        longitudes = np.tan(
            np.linspace(
                -np.pi / 2 + self.epsilon_lon, np.pi / 2 - self.epsilon_lon, shape[0]
            )
        )
        longitudes *= self.dlon / (longitudes[-1] - longitudes[0])
        longitudes += self.lon0 - longitudes[0]
        longitudes %= 360

        if len(shape) > 1:
            longitudes = np.broadcast_to(longitudes[:, None], shape)

        return longitudes

    def latitude(self, shape: tuple[int, ...]) -> np_t.NDArray[np.float64]:
        latitudes = np.sin(
            np.linspace(
                np.pi / 2 + self.epsilon_lat, 3 * np.pi / 2 - self.epsilon_lat, shape[0]
            )
        )
        latitudes *= self.lat0 / abs(np.max(latitudes))
        if len(shape) > 1:
            latitudes = np.broadcast_to(latitudes[:, None], shape)

        return latitudes

    def cycle_number(self, shape: tuple[int, ...]) -> np_t.NDArray[np.int64]:
        return np.full(shape, self._cycle_number)

    def pass_number(self, shape: tuple[int, ...]) -> np_t.NDArray[np.int64]:
        return np.full(shape, self._pass_number)

    def __getitem__(
        self, key: str
    ) -> tp.Callable[[tuple[int, ...]], np_t.NDArray[np.datetime64 | np.float64]]:
        try:
            return getattr(self, key)
        except AttributeError:
            # Return an integer full masked array. Casting to float is safe
            # Returning a float array that is later cast to int would be unsafe
            # and would trigger a warning
            return functools.partial(np.ma.masked_all, dtype=int)
