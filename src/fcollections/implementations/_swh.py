from __future__ import annotations

import re

from fcollections.core import (
    FileNameConvention,
    FileNameFieldDatetime,
    FileNameFieldEnum,
    FileNameFieldPeriod,
    FilesDatabase,
    OpenMfDataset,
    PeriodMixin,
)
from fcollections.missions import MissionsPhases

from ._definitions import DESCRIPTIONS, XARRAY_TEMPORAL_NETCDFS

SWH_PATTERN = re.compile(
    r"global_vavh_l3_rt_(?P<mission>.*)_(?P<time>\d{8}T\d{6}_\d{8}T\d{6})_(?P<production_date>\d{8}T\d{6}).nc"
)


class FileNameConventionSWH(FileNameConvention):

    def __init__(self):
        super().__init__(
            regex=SWH_PATTERN,
            fields=[
                FileNameFieldEnum(
                    "mission",
                    MissionsPhases,
                    description=("Altimetry mission in the file."),
                ),
                FileNameFieldPeriod(
                    "time", "%Y%m%dT%H%M%S", "_", description=DESCRIPTIONS["time"]
                ),
                FileNameFieldDatetime(
                    "production_date",
                    "%Y%m%dT%H%M%S",
                    description=DESCRIPTIONS["production_date"],
                ),
            ],
            generation_string="global_vavh_l3_rt_{mission!f}_{time!f}_{production_date!f}.nc",
        )


class BasicNetcdfFilesDatabaseSWH(FilesDatabase, PeriodMixin):
    """Database mapping to select and read significant wave height Netcdf files
    in a local file system."""

    parser = FileNameConventionSWH()
    reader = OpenMfDataset(XARRAY_TEMPORAL_NETCDFS)
    sort_keys = "time"


try:
    from fcollections.implementations.optional import (
        GeoOpenMfDataset,
        TemporalSerieAreaSelector,
    )

    class NetcdfFilesDatabaseSWH(BasicNetcdfFilesDatabaseSWH):
        reader = GeoOpenMfDataset(
            area_selector=TemporalSerieAreaSelector(),
            xarray_options=XARRAY_TEMPORAL_NETCDFS,
        )

except ImportError:
    import logging

    from ._definitions import MISSING_OPTIONAL_DEPENDENCIES_MESSAGE

    logger = logging.getLogger(__name__)
    logger.info(MISSING_OPTIONAL_DEPENDENCIES_MESSAGE)

    NetcdfFilesDatabaseSWH = BasicNetcdfFilesDatabaseSWH
