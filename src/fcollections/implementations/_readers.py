from __future__ import annotations

import functools
import logging
import re
import typing as tp
import warnings
from enum import Enum, auto
from functools import partial

import fsspec
import fsspec.implementations.local as fs_loc
import numpy as np
import xarray as xr

from fcollections.core import OpenMfDataset, compose

from ._definitions import SWOT_PATTERN, ProductSubset

logger = logging.getLogger(__name__)

if tp.TYPE_CHECKING:  # pragma: no cover
    from fcollections.core import GroupMetadata


class StackLevel(Enum):
    """Stack level for swath half orbits on reference grid.

    Swath half orbits on a reference grid are by definition sampled at the same
    location for each cycle. This means we can split the temporal dimension
    ``num_lines`` into one or two other dimensions ``cycle_number`` and
    ``pass_number``
    """

    #: No stack, dataset will be returned as (num_lines, num_pixels)
    NOSTACK = auto()
    #: Stack cycle, dataset will be returned as (cycle_number, num_lines,
    # num_pixels)
    CYCLES = auto()
    #: Stack half orbits, dataset will be returned as (cycle_number,
    # pass_number, num_lines, num_pixels)
    CYCLES_PASSES = auto()


class SwotReaderL3LRSSH(OpenMfDataset):
    """Reader for SWOT KaRIn L3_LR_SSH products."""

    #: SSHA Variables with nadir data clipped in it. Should cover both present
    #: and older versions of the product
    clipped_ssha: set[str] = {
        "ssha_noiseless",
        "ssha_unfiltered",
        "ssha_filtered",
        "ssha_unedited",
    }
    #: Variables we want set as coordinates in the output dataset
    expected_coords: set[str] = {"time", "longitude", "latitude"}

    def read(
        self,
        subset: ProductSubset,
        files: list[str],
        selected_variables: list[str] | None = None,
        fs: fsspec.AbstractFileSystem = fs_loc.LocalFileSystem(),
        stack: str | StackLevel = StackLevel.NOSTACK,
        swath: bool = True,
        nadir: bool = False,
        preprocessor: tp.Callable[[xr.Dataset], xr.Dataset] | None = None,
    ) -> xr.Dataset:
        """Read a dataset from L2_LR_SSH products.

        Parameters
        ----------
        files
            list of files to open. At least one file should be given
        fs
            File systems hosting the files
        selected_variables
            list of variables to select in dataset. Set to None (default) to
            disable the selection
        subset
            Product dataset (Basic, Expert, Technical or Unsmoothed)
        bbox
            the bounding box (lon_min, lat_min, lon_max, lat_max) used to select
            the data in a given area. Longitude coordinates can be provided in
            [-180, 180[ or [0, 360[ convention. If bbox's longitude crosses the
            circularity, it will be split in two subboxes to ensure a proper
            selection (e.g. longitude interval: [170, -170] -> data in
            [170, 180[ and [-180, -170] will be retrieved)
        stack
            Whether to stack the cycles and passes of the dataset. This option
            is only available for Basic, Expert and Technical datasets which are
            defined on a reference grid (fixed grid between cycles). Set to
            CYCLES_PASSES to stack both cycles and passes. Set to CYCLES to
            stack only the cycles, in which case cycles with missing passes will
            be left over. Defaults to NOSTACK
        nadir
            Whether to read the nadir data from the product. Only relevant the
            Basic and Expert subsets where the nadir data is clipped in the
            swath. Defaults to False
        swath
            Whether to read the swath data from the product. Only relevant the
            Basic and Expert subsets where the nadir data is clipped in the
            swath. Defaults to True

        Raises
        ------
        ValueError
            If stack=CYCLES_PASSES or stack=CYCLES, swath=False and nadir=True.
            In this case, we are trying to stack nadir data which is not
            guaranteed to have the same number of points per half orbit. This is
            not supported case
        ValueError
            If swath=False and nadir=False. In this case, the user is asking for
            an empty return
        ValueError
            If the input list of files is empty
        ValueError
            If the input stack parameter is not matching a valid StackLevel

        Returns
        -------
        :
            An xarray dataset containing the dataset from the input files
        """
        stack, on_reference_grid, selected_variables = self._check_inputs(
            files, stack, nadir, swath, subset, selected_variables
        )
        main_preprocessor = self._build_preprocessor(
            stack, swath, nadir, on_reference_grid
        )
        preprocessor = compose(main_preprocessor, preprocessor)

        if on_reference_grid and not swath and nadir:
            ds = self._read_expert_nadir(files, selected_variables, fs, preprocessor)
        elif on_reference_grid:
            ds = _read_expert_swath(files, selected_variables, fs, preprocessor, stack)
        else:
            ds = self._read_unsmoothed(files, selected_variables, fs, preprocessor)

        ds = ds.reset_coords()
        coords = set(ds.variables) & self.expected_coords
        return ds.set_coords(coords)

    def _build_preprocessor(
        self, stack: StackLevel, swath: bool, nadir: bool, on_reference_grid: bool
    ) -> tp.Callable[[xr.Dataset], xr.Dataset]:
        # Prepare the multiple preprocessors useful for reading
        if stack == StackLevel.NOSTACK and swath:
            __add_cycle_pass_numbers = _add_cycle_pass_numbers
        elif stack == StackLevel.NOSTACK and not swath:
            __add_cycle_pass_numbers = functools.partial(
                _add_cycle_pass_numbers,
                cycle_number_dimension="num_nadir",
                pass_number_dimension="num_nadir",
            )
        elif stack == StackLevel.CYCLES:
            __add_cycle_pass_numbers = functools.partial(
                _add_cycle_pass_numbers, cycle_number_dimension=None
            )
        elif stack == StackLevel.CYCLES_PASSES:
            __add_cycle_pass_numbers = functools.partial(
                _add_cycle_pass_numbers,
                cycle_number_dimension=None,
                pass_number_dimension=None,
            )

        __unclip_nadir = (
            partial(_unclip_nadir, variables=self.clipped_ssha) if not nadir else None
        )

        if on_reference_grid:
            if not swath and nadir:
                preprocessor = compose(
                    _cross_track_distance_coord,
                    __add_cycle_pass_numbers,
                )
            else:
                preprocessor = compose(
                    _cross_track_distance_coord,
                    __add_cycle_pass_numbers,
                    __unclip_nadir,
                    _drop_nadir_dimension,
                )
        else:
            preprocessor = compose(
                _cross_track_distance_coord,
                __add_cycle_pass_numbers,
            )

        return preprocessor

    def _read_expert_nadir(
        self,
        files: list[str],
        selected_variables: list[str] | None,
        fs: fsspec.AbstractFileSystem,
        preprocessor: tp.Callable[[xr.Dataset], xr.Dataset],
    ) -> xr.Dataset:
        if fs.protocol == ("file", "local"):
            files_opened = files
        else:
            files_opened = [fs.open(file) for file in files]

        datasets = [
            xr.load_dataset(file, engine="h5netcdf", chunks="auto")
            for file in files_opened
        ]
        datasets = filter(lambda ds: ds is not None, map(_extract_nadir, datasets))
        datasets = map(preprocessor, datasets)

        dataset = xr.concat(datasets, dim="num_nadir")
        if selected_variables is not None:
            dataset = dataset.reset_coords()[selected_variables]
        return dataset

    def _read_unsmoothed(
        self,
        files: list[str],
        selected_variables: list[str] | None,
        fs: fsspec.AbstractFileSystem,
        preprocessor: tp.Callable[[xr.Dataset], xr.Dataset],
    ):
        reader = OpenMfDataset(
            xarray_options=dict(
                engine="h5netcdf", combine="nested", concat_dim="num_lines"
            )
        )
        return reader.read(
            files=files,
            selected_variables=selected_variables,
            fs=fs,
            preprocess=preprocessor,
        )

    def _check_inputs(
        self,
        files: list[str] | list[list[str]],
        stack: StackLevel | str,
        nadir: bool,
        swath: bool,
        subset: ProductSubset,
        selected_variables: list[str] | None,
    ) -> tuple[StackLevel, bool, list[str] | None]:
        if not isinstance(stack, StackLevel):
            try:
                stack = StackLevel[stack]
            except KeyError as exc:
                msg = (
                    f"stack parameter should be one of {list(StackLevel)}, "
                    f"got {stack} instead"
                )
                raise ValueError(msg) from exc

        if selected_variables is not None:
            # Always select clipped nadir indexes. We need theses variable to
            # either extract or remoev the nadir data from the swath when asked
            selected_variables = list(selected_variables) + [
                "i_num_line",
                "i_num_pixel",
            ]

        if len(files) == 0:
            msg = (
                "Empty list of files to read: at least one valid file must " "be given"
            )
            raise ValueError(msg)

        if stack != StackLevel.NOSTACK and nadir and not swath:
            msg = (
                "Stacking L3 products by cycle or half orbits with only "
                "nadir data is not supported. Set swath=True instead"
            )
            raise ValueError(msg)

        if not swath and not nadir:
            msg = (
                "Swath data and nadir data are both deselected: set nadir "
                "and/or swath to True"
            )
            raise ValueError(msg)

        if subset in [
            ProductSubset.Basic,
            ProductSubset.Expert,
            ProductSubset.Technical,
        ]:
            return stack, True, selected_variables
        elif subset == ProductSubset.Unsmoothed:
            return stack, False, selected_variables
        else:
            msg = (
                "Expected Basic, Expert, Technical or Unsmoothed subset for "
                f"L3_LR_SSH product, got {subset}"
            )
            raise ValueError(msg)


def _read_expert_swath(
    files: list[str],
    selected_variables: list[str] | None,
    fs: fsspec.AbstractFileSystem,
    preprocessor: tp.Callable[[xr.Dataset], xr.Dataset],
    stack: StackLevel,
):
    if stack == StackLevel.NOSTACK:
        xarray_options = dict(
            combine="nested",
            concat_dim="num_lines",
            engine="h5netcdf",
            join="outer",
            data_vars="all",
            compat="no_conflicts",
        )
    else:
        xarray_options = dict(
            combine="by_coords",
            engine="h5netcdf",
            join="outer",
            data_vars="all",
            compat="no_conflicts",
        )

    reader = OpenMfDataset(xarray_options=xarray_options)
    ds = reader.read(
        files=files,
        selected_variables=selected_variables,
        fs=fs,
        preprocess=preprocessor,
    )

    # Dump the previously index inserted for helping xarray concatenate the data
    # properly
    return ds.drop_vars("num_lines", errors="ignore")


class SwotReaderL2LRSSH(OpenMfDataset):
    """Reader for SWOT KaRIn L2_LR_SSH products."""

    #: Variables we want set as coordinates in the output dataset
    expected_coords: set[str] = {"time", "longitude", "latitude"}

    def read(
        self,
        subset: ProductSubset,
        files: list[str],
        selected_variables: list[str] | None = None,
        fs: fsspec.AbstractFileSystem = fs_loc.LocalFileSystem(),
        stack: StackLevel | str = StackLevel.NOSTACK,
        left_swath: bool = True,
        right_swath: bool = False,
        preprocessor: tp.Callable[[xr.Dataset], xr.Dataset] | None = None,
    ) -> xr.Dataset:
        """Read a dataset from L2_LR_SSH products.

        Parameters
        ----------
        files
            list of files to open. At least one file should be given
        fs
            File systems hosting the files
        selected_variables
            list of variables to select in dataset. Set to None (default) to
            disable the selection
        subset
            Product dataset (Basic, Expert, WindWave or Unsmoothed)
        bbox
            the bounding box (lon_min, lat_min, lon_max, lat_max) used to select
            the data in a given area. Longitude coordinates can be provided in
            [-180, 180[ or [0, 360[ convention. If bbox's longitude crosses the
            circularity, it will be split in two subboxes to ensure a proper
            selection (e.g. longitude interval: [170, -170] -> data in
            [170, 180[ and [-180, -170] will be retrieved)
        left_swath
            Whether to load the left side of the swath for Unsmoothed datasets.
            Set to False in conjunction to right_swath will disable swath
            reading for Expert and Basic dataset
        right_swath
            Whether to load the right side of the swath for Unsmoothed datasets.
            Set to False in conjunction to right_swath will disable swath
            reading for Expert and Basic dataset
        stack
            Whether to stack the cycles and passes of the dataset. This option
            is only available for Basic, Expert and WindWave datasets which are
            defined on a reference grid (fixed grid between cycles). Set to
            CYCLES_PASSES to stack both cycles and passes. Set to CYCLES to
            stack only the cycles, in which case cycles with missing passes will
            be left over. Defaults to NOSTACK

        Raises
        ------
        ValueError
            If the input list of files is empty
        ValueError
            If the input stack parameter is not matching a valid StackLevel

        Returns
        -------
            An xarray dataset containing the dataset from the input files
        """
        stack, on_reference_grid = self._check_inputs(
            files, left_swath, right_swath, subset, stack
        )
        main_preprocessor = self._build_preprocessor(stack)
        preprocessor = compose(main_preprocessor, preprocessor)

        if on_reference_grid:
            ds = _read_expert_swath(files, selected_variables, fs, preprocessor, stack)
        else:
            ds = self._read_unsmoothed(
                files, selected_variables, fs, preprocessor, right_swath
            )

        ds = ds.reset_coords()
        coords = set(ds.variables) & self.expected_coords
        return ds.set_coords(coords)

    def _check_inputs(
        self,
        files: list[str] | list[list[str]],
        left_swath: bool,
        right_swath: bool,
        subset: ProductSubset,
        stack: StackLevel | str,
    ) -> tuple[StackLevel, bool]:
        if not isinstance(stack, StackLevel):
            try:
                stack = StackLevel[stack]
            except KeyError as exc:
                msg = (
                    f"stack parameter should be one of {list(StackLevel)}, "
                    f"got {stack} instead"
                )
                raise ValueError(msg) from exc

        if len(files) == 0:
            msg = (
                "Empty list of files to read: at least one valid file must " "be given"
            )
            raise ValueError(msg)

        if left_swath and right_swath:
            warnings.warn(
                "Cannot combine left and right sides of the swath, "
                "only the left side will be returned. Set left_swath=False and "
                "right_swath=True to retrieve the other side"
            )
        elif not left_swath and not right_swath:
            warnings.warn("No swath side selecting, returning left side by " "default")

        if subset in [
            ProductSubset.Basic,
            ProductSubset.Expert,
            ProductSubset.WindWave,
        ]:
            return stack, True
        elif subset == ProductSubset.Unsmoothed:
            return stack, False
        else:
            msg = (
                "Expected Basic, Expert, Technical or Unsmoothed subset for "
                f"L3_LR_SSH product, got {subset}"
            )
            raise ValueError(msg)

    def _build_preprocessor(
        self, stack: StackLevel
    ) -> tp.Callable[[xr.Dataset], xr.Dataset]:
        # Prepare the multiple preprocessors useful for reading
        if stack == StackLevel.NOSTACK:
            __add_cycle_pass_numbers = _add_cycle_pass_numbers
        elif stack == StackLevel.CYCLES:
            __add_cycle_pass_numbers = functools.partial(
                _add_cycle_pass_numbers, cycle_number_dimension=None
            )
        else:
            __add_cycle_pass_numbers = functools.partial(
                _add_cycle_pass_numbers,
                cycle_number_dimension=None,
                pass_number_dimension=None,
            )

        preprocessor = __add_cycle_pass_numbers
        return preprocessor

    def _read_unsmoothed(
        self,
        files: list[str],
        selected_variables: list[str] | None,
        fs: fsspec.AbstractFileSystem,
        preprocessor: tp.Callable[[xr.Dataset], xr.Dataset],
        right_swath: bool,
    ) -> xr.Dataset:
        reader = OpenMfDataset(
            xarray_options=dict(
                engine="h5netcdf",
                combine="nested",
                concat_dim="num_lines",
                # Read left swath if nothing is asked. We may raise an exception in
                # the future to request proper inputs from the user
                group="left" if not right_swath else "right",
            )
        )
        return reader.read(
            files=files,
            selected_variables=selected_variables,
            fs=fs,
            preprocess=preprocessor,
        )


def _drop_nadir_dimension(ds: xr.Dataset) -> xr.Dataset:
    if "num_nadir" in ds.dims:
        return ds.drop_dims("num_nadir")
    return ds


def _cross_track_distance_coord(ds: xr.Dataset) -> xr.Dataset:

    # Concatenation done with open_mfdataset cannot have a fine control
    # with nested concatenation. Meaning, the 'data_vars' argument will
    # be the same for both concatenation. The cross_track_distance is
    # fixed and is set as a coordinate to prevent xarray from expanding
    # it
    if "cross_track_distance" in ds:
        return ds.assign_coords(cross_track_distance=ds.cross_track_distance)
    return ds


def _unclip_nadir(ds: xr.Dataset, variables: set[str]) -> xr.Dataset:
    variables = variables & set(ds.variables)
    if "num_nadir" not in ds.dims or len(variables) == 0:
        return ds

    mask = np.zeros((ds.num_lines.size, ds.num_pixels.size), dtype=bool)
    mask[ds["i_num_line"].values, ds["i_num_pixel"].values] = True
    mask = xr.DataArray(mask, dims=("num_lines", "num_pixels"))
    ds.update(ds[variables].where(~mask))
    return ds


def _extract_nadir(ds: xr.Dataset) -> xr.Dataset | None:
    try:
        return ds.isel(
            num_lines=ds["i_num_line"].compute(), num_pixels=ds["i_num_pixel"].compute()
        )
    except KeyError:
        logger.debug(
            "Missing i_num_line or i_num_pixel in dataset. Nadir extraction skipped"
        )
    except ValueError as exc:
        msg = (
            f"Nadir extraction failed, dataset has an unsupported structure {ds.sizes}"
        )
        warnings.warn(msg)
        logger.exception(exc)

    return None


def _add_cycle_pass_numbers(
    ds: xr.Dataset,
    cycle_number_dimension: str | None = "num_lines",
    pass_number_dimension: str | None = "num_lines",
) -> xr.Dataset:
    try:
        result = re.search(SWOT_PATTERN, ds.encoding["source"])
        cycle_number = np.uint16(result.group("cycle_number"))
        pass_number = np.uint16(result.group("pass_number"))
    except KeyError as exc:
        msg = (
            "Could not deduce the cycle_number and pass_number from the "
            "input dataset because the source in missing in the encoding"
        )
        raise ValueError(msg) from exc
    except AttributeError as exc:
        encoding = ds.encoding["source"]
        msg = (
            "Could not deduce the cycle_number and pass_number from the "
            f'input dataset, the filename "{encoding}" does '
            f"not match the expected pattern {SWOT_PATTERN}"
        )
        raise ValueError(msg) from exc

    def add_dimension(ds: xr.Dataset, variable: str, value: int, dimension: str | None):
        if dimension is None:
            ds = ds.assign_coords({variable: (variable, [value])})
        else:
            try:
                ds = ds.assign_coords(
                    {
                        variable: (
                            dimension,
                            np.zeros(ds.sizes[dimension], dtype=np.uint8) + value,
                        )
                    }
                )
            except KeyError as exc:
                msg = (
                    f"Could not add {variable} to the input dataset: "
                    f"missing {dimension} dimension"
                )
                raise ValueError(msg) from exc
        return ds

    ds = add_dimension(ds, "cycle_number", cycle_number, cycle_number_dimension)
    ds = add_dimension(ds, "pass_number", pass_number, pass_number_dimension)

    # CYCLES stacking detected when cycle_number_dimension is None (a
    # cycle_number dimension is created) but pass_number_dimension is valid (a
    # pass_number variable is created)
    if cycle_number_dimension is None and pass_number_dimension is not None:
        # Stacking half orbit needs a reference grid which has exactly the same
        # number of samples per half orbits (9866 for L2_LR_SSH and 9860 for
        # L3_LR_SSH). This is a strong hypothesis that we use to create a non
        # duplicate cycle index for each half orbit
        half_orbit_size = np.uint64(ds.sizes["num_lines"])
        # We build an index for the num_lines. In case we want to stack cycles
        # using xr.combine_by_coords, we need both 'cycle_number' and
        # 'num_lines' indexes for xarray to perform a robust combination. In
        # case we want to stack cycles and passes, we need both 'cycle_number'
        # and 'pass_number' indexes
        ds["num_lines"] = range(
            pass_number * half_orbit_size, (pass_number + 1) * half_orbit_size
        )
    return ds


class SwotReaderL3WW(OpenMfDataset):
    """Reader for the SWOT L3_LR_WIND_WAVE product.

    This reader handles both the Light and Extended subsets. The Light subset is
    simpler and has spectral content along the n_box dimension with a default
    tile and box sizes. The Extended subset has multiple tile and box sizes
    stored in matching netcdf groups. Thus, tile and box size should generally
    be given for the Extended subset (see the read method for more details).

    The L3_LR_WIND_WAVE product is built from the L3_LR_SSH product, and
    references 'num_lines' indices.

    See Also
    --------
    SwotReaderL3LRSSH: the L3_LR_SSH product reader
    """

    def read(
        self,
        subset: ProductSubset,
        files: list[str],
        selected_variables: list[str] | None = None,
        fs: fsspec.AbstractFileSystem = fs_loc.LocalFileSystem(),
        tile: int | None = None,
        box: int | None = None,
        preprocessor: tp.Callable[[xr.Dataset], xr.Dataset] | None = None,
    ) -> xr.Dataset:
        """Read a SWOT dataset from LR_SSH products.

        Parameters
        ----------
        files
            list of files to open. At least one file should be given. If
            multiple files are given, variables following the n_box dimension
            will be concatenated. The others variables are constant and will not
            be repeated
        fs
            File systems hosting the files
        selected_variables
            list of variables to select in dataset. Set to None (default) to
            disable the selection
        subset
            Product dataset (Light, Extended)
        bbox
            the bounding box (lon_min, lat_min, lon_max, lat_max) used to select
            the data in a given area. Longitude coordinates can be provided in
            [-180, 180[ or [0, 360[ convention. If bbox's longitude crosses the
            circularity, it will be split in two subboxes to ensure a proper
            selection (e.g. longitude interval: [170, -170] -> data in
            [170, 180[ and [-180, -170] will be retrieved)
        tile
            Tile size of the spectrum computation. Is mandatory for the Extended
            subset
        box
            Box size of the spectrum computation. Is mandatory for the Extended
            subset if one the requested variables is defined along the n_box
            dimension

        Raises
        ------
        ValueError
            If tile or box argument are given when reading a Light subset
        ValueError
            If the list of files is empty
        ValueError
            If the tile and box argument is missing for the Extended subset
        ValueError
            If the input subset does not match neither Light nor Extended
        ValueError
            If the input tile or box size is not found in the files

        Returns
        -------
            An xarray dataset containing the dataset from the input files
        """

        if len(files) == 0:
            msg = (
                "Empty list of files to read: at least one valid file must " "be given"
            )
            raise ValueError(msg)

        if subset == ProductSubset.Light:
            return self._read_light(
                files, selected_variables, preprocessor, fs, tile, box
            )
        elif subset == ProductSubset.Extended:
            return self._read_extended(
                files, selected_variables, preprocessor, fs, tile, box
            )
        else:
            msg = (
                "Expected Light or Extended subset for L3_LR_WIND_WAVE "
                f"product, got {subset}"
            )
            raise ValueError(msg)

    def _read_light(
        self,
        files: list[str],
        selected_variables: list[str] | None,
        preprocessor: tp.Callable[[xr.Dataset], xr.Dataset] | None,
        fs: fsspec.AbstractFileSystem,
        tile: int | None,
        box: int | None,
    ) -> xr.Dataset:
        if tile is not None or box is not None:
            msg = (
                "'tile' and 'box' arguments must be None when reading a "
                "Light subset of the L3_LR_WIND_WAVE product"
            )
            raise ValueError(msg)

        reader = OpenMfDataset(
            xarray_options=dict(
                engine="h5netcdf",
                data_vars="minimal",
                compat="no_conflicts",
                coords="different",
                combine="nested",
                concat_dim="n_box",
            )
        )
        return reader.read(
            files=files,
            selected_variables=selected_variables,
            fs=fs,
            preprocess=preprocessor,
        )

    def _read_extended(
        self,
        files: list[str],
        selected_variables: list[str] | None,
        preprocessor: tp.Callable[[xr.Dataset], xr.Dataset] | None,
        fs: fsspec.AbstractFileSystem,
        tile: int | None,
        box: int | None,
    ) -> xr.Dataset:
        group_metadata = self.metadata(files[0], fs)

        # We should find no root variables in v2.0 of the Extended product.
        # It is expected to find it starting from v2.0.1
        _, tile_group, box_group = self._identify_root_tile_box_variables(
            group_metadata, selected_variables, tile, box
        )

        if tile_group is not None:
            reader = OpenMfDataset(
                dict(
                    engine="h5netcdf",
                    group=tile_group[0],
                )
            )
            ds_tile = reader.read(
                files=[files[0]], selected_variables=tile_group[1], fs=fs
            )
        else:
            ds_tile = xr.Dataset()

        if box_group is not None:
            reader = OpenMfDataset(
                xarray_options=dict(
                    engine="h5netcdf",
                    combine="nested",
                    concat_dim="n_box",
                    group=box_group[0],
                )
            )
            ds_box = reader.read(
                files=files,
                selected_variables=box_group[1],
                preprocess=preprocessor,
                fs=fs,
            )
        else:
            ds_box = xr.Dataset()

        ds_tile.update(ds_box)
        return ds_tile

    def _identify_root_tile_box_variables(
        self,
        group_metadata: GroupMetadata,
        selected_variables: set[str] | None,
        tile: int | None,
        box: int | None,
    ) -> tuple[
        tuple[str | None, set[str] | None],
        tuple[str, set[str] | None],
        tuple[str | None, set[str] | None],
    ]:

        if selected_variables is None and (tile is None or box is None):
            msg = (
                "'tile' and 'box' arguments can't be None when "
                "'selected_variables' is not given for the "
                "L3_LR_WIND_WAVE Extended subset"
            )
            raise ValueError(msg)
        elif selected_variables is None:
            # Check groups exist
            tile_group_name = f"tile_{tile}km"
            list(group_metadata.nodes(tile_group_name))
            box_group_name = tile_group_name + f"/box_{box}km"
            list(group_metadata.nodes(box_group_name))
            return (None, None), (tile_group_name, None), (box_group_name, None)
        elif selected_variables is not None:
            remaining_variables = set(selected_variables)

            root_variables = {
                v.name for v in group_metadata.variables
            } & remaining_variables
            remaining_variables -= root_variables
            if len(remaining_variables) == 0:
                return (None, root_variables), None, None
            elif tile is None:
                msg = (
                    "Must look in tile groups for requested variables "
                    f"{remaining_variables} but 'tile' argument is set to "
                    "None"
                )
                raise ValueError(msg)

            tile_group_name = f"tile_{tile}km"
            *_, tile_group = group_metadata.nodes(tile_group_name)
            tile_variables = {
                v.name for v in tile_group.variables
            } & remaining_variables
            logger.debug(
                "Variables %s loaded from tile group %s",
                tile_variables,
                tile_group_name,
            )

            remaining_variables -= tile_variables
            if len(remaining_variables) == 0:
                return (None, root_variables), (tile_group_name, tile_variables), None
            elif box is None:
                msg = (
                    "Must look in box groups for requested variables "
                    f"{remaining_variables} but 'box' argument is set to "
                    "None"
                )
                raise ValueError(msg)

            box_group_name = f"box_{box}km"
            *_, box_group = tile_group.nodes(box_group_name)
            box_variables = {v.name for v in box_group.variables} & remaining_variables
            logger.debug(
                "Variables %s loaded from box group %s", box_variables, box_group_name
            )
            return (
                (None, root_variables),
                (tile_group_name, tile_variables),
                (tile_group_name + "/" + box_group_name, box_variables),
            )
