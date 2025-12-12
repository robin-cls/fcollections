from __future__ import annotations

import re

from fcollections.core import (
    FileNameConvention,
    FileNameFieldDatetime,
    FilesDatabase,
    OpenMfDataset,
    PeriodMixin,
)

from ._definitions import DESCRIPTIONS, XARRAY_TEMPORAL_NETCDFS_NO_BACKEND

OHC_PATTERN = re.compile(
    r"OHC-NAQG3_v(.*)r(.*)_blend_s(.*)_e(.*)_c(?P<time>\d{8})(.*).nc"
)


class FileNameConventionOHC(FileNameConvention):

    def __init__(self):
        super().__init__(
            regex=OHC_PATTERN,
            fields=[
                FileNameFieldDatetime(
                    "time", "%Y%m%d", description=DESCRIPTIONS["time"]
                ),
            ],
        )


class _NetcdfFilesDatabaseOHC(FilesDatabase, PeriodMixin):
    """Database mapping to select and read ocean heat content Netcdf files in a
    local file system.

    Attributes
    ----------
    path: str
        path to directory containing NetCDF files
    """

    parser = FileNameConventionOHC()
    reader = OpenMfDataset(XARRAY_TEMPORAL_NETCDFS_NO_BACKEND)
    sort_keys = "time"


try:
    from fcollections.implementations.optional import AreaSelector2D, GeoOpenMfDataset

    class NetcdfFilesDatabaseOHC(_NetcdfFilesDatabaseOHC):
        reader = GeoOpenMfDataset(
            area_selector=AreaSelector2D(),
            xarray_options=XARRAY_TEMPORAL_NETCDFS_NO_BACKEND,
        )

    NetcdfFilesDatabaseOHC.__doc__ = _NetcdfFilesDatabaseOHC.__doc__

except ImportError:
    import warnings

    from ._definitions import MISSING_OPTIONAL_DEPENDENCIES_MESSAGE

    warnings.warn(MISSING_OPTIONAL_DEPENDENCIES_MESSAGE)
    NetcdfFilesDatabaseOHC = _NetcdfFilesDatabaseOHC
