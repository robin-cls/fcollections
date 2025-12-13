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


class BasicNetcdfFilesDatabaseMUR(FilesDatabase, PeriodMixin):
    """Database mapping to select and read GHRSST Level 4 MUR Global Foundation
    Sea Surface Temperature Analysis product Netcdf file in a local file
    system."""

    parser = FileNameConventionMUR()
    reader = OpenMfDataset(XARRAY_TEMPORAL_NETCDFS)
    sort_keys = "time"


try:
    from fcollections.implementations.optional import AreaSelector2D, GeoOpenMfDataset

    class NetcdfFilesDatabaseMUR(BasicNetcdfFilesDatabaseMUR):
        reader = GeoOpenMfDataset(
            area_selector=AreaSelector2D(longitude="lon", latitude="lat"),
            xarray_options=XARRAY_TEMPORAL_NETCDFS,
        )

except ImportError:
    import logging

    from ._definitions import MISSING_OPTIONAL_DEPENDENCIES_MESSAGE

    logger = logging.getLogger(__name__)
    logger.info(MISSING_OPTIONAL_DEPENDENCIES_MESSAGE)

    NetcdfFilesDatabaseMUR = BasicNetcdfFilesDatabaseMUR
