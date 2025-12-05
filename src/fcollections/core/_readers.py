from __future__ import annotations

import logging
import typing as tp
import warnings
from abc import ABC, abstractmethod

import fsspec
import fsspec.implementations.local as fs_loc
import netCDF4 as nc4
import xarray as xr

from ._metadata import GroupMetadata, group_metadata_from_netcdf

logger = logging.getLogger(__name__)


def compose(
    func1: tp.Callable[[xr.Dataset], xr.Dataset],
    *func2: tp.Callable[[xr.Dataset], xr.Dataset] | None,
) -> tp.Callable[[xr.Dataset], xr.Dataset]:
    """Compose multiple functions that preprocess an xarray Dataset.

    Before calling xr.open_mfdataset, it is useful to set up various
    preprocessings. For example, one might want to crop a subset of the dataset,
    and then create an index before xarray combination steps in.

    This method is an utility that will make it easier to chain such
    preprocessors.

    The call order is the same as the input arguments: func1 is called first,
    func2[0] is called second and so on.

    Parameters
    ----------
    func1
        First preprocessor. Cannot be None
    *func2
        Subsequent preprocessors. None elements will be ignored

    Returns
    -------
    :
        The chained functions

    See Also
    --------
    xarray.open_mfdataset: method that takes chained preprocessors as an input
    """
    func2 = [f for f in func2 if f is not None]
    if len(func2) < 1:
        return func1
    if len(func2) == 1:
        return lambda x: func2[0](func1(x))
    else:
        return compose(lambda x: func2[0](func1(x)), *func2[1:])


class IFilesReader(ABC):
    """Interface for reading multiple files on a specific file system.

    Implementations of this interface can be called to peek at the
    metadata of a dataset, or to read a selection of variables.
    """

    @abstractmethod
    def read(
        self,
        files: list[str] | list[list[str]],
        selected_variables: list[str] | None = None,
        fs: fsspec.AbstractFileSystem = fs_loc.LocalFileSystem(),
        **kwargs: tp.Any,
    ) -> xr.Dataset:
        """Read a list of files.

        Parameters
        ----------
        files
            List of the files to read
        selected_variables
            Variables that needs to be read. Set to None to read everything
        fs
            File system hosting the files

        Returns
        -------
        :
            An xarray dataset containing the selected variables
        """

    @abstractmethod
    def metadata(
        self, file: str, fs: fsspec.AbstractFileSystem = fs_loc.LocalFileSystem()
    ) -> GroupMetadata:
        """Load the metadata of the given file.

        Useful to get information about the structure of the dataset, and which
        variables, dimensions and coordinates are available for reading.

        Parameters
        ----------
        file
            File from which the metadata is read
        fs
            File system hosting the file

        Returns
        -------
        :
            A GroupMetadata containing the variables, dimensions, attributes and
            subgroups
        """


def _map_nested(func, list0):
    if len(list0) > 0 and isinstance(list0[0], list):
        return [_map_nested(func, nested_list) for nested_list in list0]
    else:
        return [func(element) for element in list0]


class OpenMfDataset(IFilesReader):
    """Xarray implementation of IFilesReader interface.

    This implementation is a simple wrapper around the ``xarray.open_mfdataset``
    function. The function parameters are expected to be given as a dictionary
    of the reader, except for the ``preprocessor`` argument that should be given
    to the ``read`` method.

    Parameters
    ----------
    xarray_options
        ``xarray.open_mfdataset`` reading options. Set to None to keep xarray
        defaults

    See Also
    --------
    xarray.open_mfdataset: The wrapped reading function
    """

    def __init__(self, xarray_options: dict[str, str] | None = None):
        self.xarray_options: dict[str, str] = (
            {} if xarray_options is None else xarray_options
        )

    def read(
        self,
        files: list[str] | list[list[str]],
        selected_variables: list[str] | None = None,
        fs: fsspec.AbstractFileSystem = fs_loc.LocalFileSystem(),
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
        fs
            File system hosting the files
        preprocess
            Preprocessor for open_mfdataset

        Returns
        -------
        :
            An xarray dataset containing the selected variables
        """

        class Counter:

            def __init__(self):
                self.count = 0

            def increment(self, x):
                self.count += 1

        counter = Counter()
        _map_nested(counter.increment, files)
        logger.info("Files to read: %d", counter.count)

        with warnings.catch_warnings():
            if fs.protocol == ("file", "local"):
                files_opened = files
            else:
                files_opened = _map_nested(fs.open, files)
            drop_variables = self._selected_to_dropped(
                files_opened, selected_variables, self.xarray_options.get("group", None)
            )

            # time and time_tai can contain NaT and this triggers a Runtime
            # warning from xarray. We ignore this for the moment but we might
            # interpolate the times later
            warnings.filterwarnings(
                "ignore", category=RuntimeWarning, module="xarray.coding.times"
            )

            warnings.filterwarnings(
                "ignore", category=FutureWarning, module="xarray.core"
            )

            return xr.open_mfdataset(
                files_opened,
                drop_variables=drop_variables,
                **self.xarray_options,
                preprocess=preprocess,
            )

    def _selected_to_dropped(
        self, files: list[str], selected_variables: list[str] | None, group: str | None
    ) -> None | list[str]:
        if len(files) == 0:
            return []

        # Handle one level of nested files
        first_file = (
            files[len(files) - 1][0]
            if isinstance(files[len(files) - 1], list)
            else files[len(files) - 1]
        )

        # Convert selected variables to drop variables
        drop_variables = (
            [
                k
                for k in xr.open_dataset(first_file, group=group).variables
                if k not in selected_variables
            ]
            if selected_variables is not None
            else []
        )

        return drop_variables

    def metadata(
        self, file: str, fs: fsspec.AbstractFileSystem = fs_loc.LocalFileSystem()
    ) -> GroupMetadata:
        with fs.open(file, "rb") as f:
            with nc4.Dataset("placeholder.nc", mode="r", memory=f.read()) as nds:
                group = group_metadata_from_netcdf(nds)
        return group
