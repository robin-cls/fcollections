from __future__ import annotations

import re

from fcollections.core import (
    FileNameConvention,
    FileNameFieldDatetime,
    FilesDatabase,
    OpenMfDataset,
    PeriodMixin,
)

from ._definitions import DESCRIPTIONS, XARRAY_TEMPORAL_NETCDFS

ERA5_PATTERN = re.compile(r"reanalysis-era5-single-levels_(?P<time>\d{8}).nc")


class FileNameConventionERA5(FileNameConvention):

    def __init__(self):
        super().__init__(
            regex=ERA5_PATTERN,
            fields=[
                FileNameFieldDatetime(
                    "time", "%Y%m%d", description=DESCRIPTIONS["time"]
                )
            ],
            generation_string="reanalysis-era5-single-levels_{time!f}.nc",
        )


class NetcdfFilesDatabaseERA5(FilesDatabase, PeriodMixin):
    """Database mapping to select and read ERA5 reanalysis product Netcdf files
    in a local file system."""

    parser = FileNameConventionERA5()
    reader = OpenMfDataset(xarray_options=XARRAY_TEMPORAL_NETCDFS)
    sort_keys = "time"
