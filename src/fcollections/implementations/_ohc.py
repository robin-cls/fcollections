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


class BasicNetcdfFilesDatabaseOHC(FilesDatabase, PeriodMixin):
    """Database mapping to select and read ocean heat content Netcdf files in a
    local file system."""

    parser = FileNameConventionOHC()
    reader = OpenMfDataset(XARRAY_TEMPORAL_NETCDFS_NO_BACKEND)
    sort_keys = "time"


try:
    from fcollections.implementations.optional import AreaSelector2D, GeoOpenMfDataset

    class NetcdfFilesDatabaseOHC(BasicNetcdfFilesDatabaseOHC):
        reader = GeoOpenMfDataset(
            area_selector=AreaSelector2D(),
            xarray_options=XARRAY_TEMPORAL_NETCDFS_NO_BACKEND,
        )

except ImportError:
    import logging

    from ._definitions import MISSING_OPTIONAL_DEPENDENCIES_MESSAGE

    logger = logging.getLogger(__name__)
    logger.info(MISSING_OPTIONAL_DEPENDENCIES_MESSAGE)

    NetcdfFilesDatabaseOHC = BasicNetcdfFilesDatabaseOHC
