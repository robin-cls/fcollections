from __future__ import annotations

import functools
import typing as tp
from functools import partial

import fsspec
import fsspec.implementations.local as fs_loc
import xarray as xr

from fcollections.core import OpenMfDataset, compose
from fcollections.implementations._definitions import ProductSubset
from fcollections.implementations._readers import (
    StackLevel,
    SwotReaderL2LRSSH,
    SwotReaderL3LRSSH,
    SwotReaderL3WW,
)

from ._area_selectors import SwathAreaSelector, TemporalSerieAreaSelector
from ._model import IAreaSelector


class GeoOpenMfDataset(OpenMfDataset):
    """Extension of the OpenMfDataset reader.

    Bring geographical awareness to the reader. In case a bounding box is given
    to the reader, the IAreaSelector is used to update the xarray preprocessor.

    Parameters
    ----------
    area_selector
        Area selection callable generator
    xarray_options
        ``xarray.open_mfdataset`` reading options. Set to None to keep xarray
        defaults

    See Also
    --------
    fcollections.core.IAreaSelector
        Interface for defining the area selection callable
    xarray.open_mfdataset
        The wrapped reading function
    """

    def __init__(
        self, area_selector: IAreaSelector, xarray_options: dict[str, str] | None = None
    ):
        self.area_selector = area_selector
        super().__init__(xarray_options)

    def read(
        self,
        files: list[str] | list[list[str]],
        selected_variables: list[str] | None = None,
        fs: fsspec.AbstractFileSystem = fs_loc.LocalFileSystem(),
        bbox: tuple[float, float, float, float] | None = None,
        preprocess: tp.Callable[[xr.Dataset], xr.Dataset] | None = None,
        **kwargs: tp.Any,
    ) -> xr.Dataset:
        """Read a list of files.

        Parameters
        ----------
        files
            List of the files to read
        selected_variables
            Variables that needs to be read. Set to None to read everything
        bbox
            the bounding box (lon_min, lat_min, lon_max, lat_max) used to subset data
            Longitude coordinates can be provided in [-180, 180[ or [0, 360[ convention.
            If bbox's longitude crosses the -180/180 of longitude, data around the crossing and matching the bbox will be selected.
            (e.g. longitude interval: [170, -170] -> data in [170, 180[ and [-180, -170] will be retrieved)
        fs
            File system hosting the files
        preprocess
            Preprocessor for open_mfdataset

        Returns
        -------
        :
            An xarray dataset containing the selected variables
        """
        if bbox:
            apply_bounds = partial(self.area_selector.apply, bbox=bbox)
            preprocess = compose(apply_bounds, preprocess)

        return super().read(
            files=files,
            selected_variables=selected_variables,
            fs=fs,
            preprocess=preprocess,
        )


class GeoSwotReaderL2LRSSH(SwotReaderL2LRSSH):
    """Extension of the SwotReaderL2LRSSH reader.

    Bring geographical awareness to the reader. In case a bounding box is given
    to the reader, the IAreaSelector is used to update the xarray preprocessor.

    See Also
    --------
    fcollections.core.IAreaSelector
        Interface for defining the area selection callable
    """

    def read(
        self,
        subset: ProductSubset,
        files: list[str],
        selected_variables: list[str] | None = None,
        fs: fsspec.AbstractFileSystem = fs_loc.LocalFileSystem(),
        stack: StackLevel | str = StackLevel.NOSTACK,
        left_swath: bool = True,
        right_swath: bool = False,
        bbox: tuple[float, float, float, float] | None = None,
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
        _crop_area = (
            functools.partial(SwathAreaSelector().apply, bbox=bbox)
            if bbox is not None
            else None
        )

        return super().read(
            subset,
            files,
            selected_variables,
            fs,
            stack,
            left_swath,
            right_swath,
            preprocessor=_crop_area,
        )


class GeoSwotReaderL3LRSSH(SwotReaderL3LRSSH):
    """Extension of the SwotReaderL3LRSSH reader.

    Bring geographical awareness to the reader. In case a bounding box is given
    to the reader, the IAreaSelector is used to update the xarray preprocessor.

    See Also
    --------
    fcollections.core.IAreaSelector
        Interface for defining the area selection callable
    """

    def read(
        self,
        subset: ProductSubset,
        files: list[str] | list[list[str]],
        selected_variables: list[str] | None = None,
        fs: fsspec.AbstractFileSystem = fs_loc.LocalFileSystem(),
        stack: str | StackLevel = StackLevel.NOSTACK,
        swath: bool = True,
        nadir: bool = False,
        bbox: tuple[float, float, float, float] | None = None,
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
        _crop_area = self._build_additionnal_preprocessor(swath, nadir, bbox)
        return super().read(
            subset,
            files,
            selected_variables,
            fs,
            stack,
            swath,
            nadir,
            preprocessor=_crop_area,
        )

    def _build_additionnal_preprocessor(
        self, swath: bool, nadir: bool, bbox: tuple[float, float, float, float] | None
    ) -> tp.Callable[[xr.Dataset], xr.Dataset] | None:
        if bbox is None:
            return None

        if not swath and nadir:
            _crop_area = partial(
                TemporalSerieAreaSelector(dimension="num_nadir").apply, bbox=bbox
            )
        else:
            _crop_area = partial(SwathAreaSelector().apply, bbox=bbox)

        return _crop_area


class GeoSwotReaderL3WW(SwotReaderL3WW):
    """Extension of the SwotReaderL3WW reader.

    Bring geographical awareness to the reader. In case a bounding box is given
    to the reader, the IAreaSelector is used to update the xarray preprocessor.

    See Also
    --------
    fcollections.core.IAreaSelector
        Interface for defining the area selection callable
    """

    def read(
        self,
        subset: ProductSubset,
        files: list[str],
        selected_variables: list[str] | None = None,
        fs: fsspec.AbstractFileSystem = fs_loc.LocalFileSystem(),
        tile: int | None = None,
        box: int | None = None,
        bbox: tuple[float, float, float, float] | None = None,
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
        _crop_area = (
            functools.partial(
                TemporalSerieAreaSelector(dimension="n_box").apply, bbox=bbox
            )
            if bbox is not None
            else None
        )

        return super().read(
            subset, files, selected_variables, fs, tile, box, preprocessor=_crop_area
        )
