from __future__ import annotations

import re
from typing import TYPE_CHECKING

import fsspec
import fsspec.implementations.local as fs_loc
import numpy as np

from fcollections.core import (
    DiscreteTimesMixin,
    FileNameConvention,
    FileNameFieldDateJulian,
    FilesDatabase,
    OpenMfDataset,
)

from ._definitions import XARRAY_TEMPORAL_NETCDFS_NO_BACKEND

if TYPE_CHECKING:
    from pathlib import Path


DAC_PATTERN = re.compile(r"dac_dif_((\d+)days_){0,1}(?P<time>\d{5}_\d{2}).nc")


class FileNameConventionDAC(FileNameConvention):

    def __init__(self):
        super().__init__(
            regex=DAC_PATTERN,
            fields=[
                FileNameFieldDateJulian(
                    "time",
                    reference=np.datetime64("1950-01-01T00"),
                    julian_day_format="days_hours",
                )
            ],
            generation_string="dac_dif_{time!f}.nc",
        )


class _NetcdfFilesDatabaseDAC(FilesDatabase, DiscreteTimesMixin):
    """Database mapping to select and read Dynamic atmospheric correction
    Netcdf files in a local file system.

    Attributes
    ----------
    path: str
        path to directory containing NetCDF files
    """

    parser = FileNameConventionDAC()
    reader = OpenMfDataset(XARRAY_TEMPORAL_NETCDFS_NO_BACKEND)
    metadata_injection = {"time": ("time",)}
    sort_keys = ["time"]

    def __init__(
        self, path: Path, fs: fsspec.AbstractFileSystem = fs_loc.LocalFileSystem()
    ):
        super().__init__(path, fs)
        super(FilesDatabase, self).__init__(np.timedelta64(6, "h"))
