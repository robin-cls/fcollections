from __future__ import annotations

import re

from fcollections.core import (
    FileNameConvention,
    FileNameFieldDatetime,
    FilesDatabase,
    OpenMfDataset,
    PeriodMixin,
)

from ._collections import _XARRAY_TEMPORAL_NETCDFS
from ._conventions import DESCRIPTIONS

MUR_PATTERN = re.compile(
    r"(?P<time>\d{8}\d{6})-JPL-L4_GHRSST-SSTfnd-MUR-GLOB-v(.*)-fv(.*).nc"
)


class FileNameConventionMUR(FileNameConvention):

    def __init__(self):
        super().__init__(
            regex=MUR_PATTERN,
            fields=[
                FileNameFieldDatetime(
                    "time", "%Y%m%d%H%M%S", description=DESCRIPTIONS["time"]
                )
            ],
            generation_string="{time!f}-JPL-L4_GHRSST-SSTfnd-MUR-GLOB-v02.0-fv04.1.nc",
        )


class _NetcdfFilesDatabaseMUR(FilesDatabase, PeriodMixin):
    """Database mapping to select and read GHRSST Level 4 MUR Global Foundation
    Sea Surface Temperature Analysis product Netcdf file in a local file
    system.

    Attributes
    ----------
    path: str
        path to directory containing NetCDF files
    """

    parser = FileNameConventionMUR()
    reader = OpenMfDataset(_XARRAY_TEMPORAL_NETCDFS)
    sort_keys = "time"
