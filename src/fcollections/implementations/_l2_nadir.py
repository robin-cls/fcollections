from __future__ import annotations

import re

from fcollections.core import (
    FileNameConvention,
    FileNameFieldInteger,
    FileNameFieldPeriod,
    FilesDatabase,
    OpenMfDataset,
    PeriodMixin,
)

from ._definitions import DESCRIPTIONS, XARRAY_TEMPORAL_NETCDFS

L2_NADIR_PATTERN = re.compile(
    r"SWOT_(GPN|IPN)_2PfP(?P<cycle_number>\d{3})_(?P<pass_number>\d{3})_(?P<time>\d{8}_\d{6}_\d{8}_\d{6}).nc"
)


class FileNameConventionL2Nadir(FileNameConvention):
    """L2 Nadir datafiles parser."""

    def __init__(self):
        super().__init__(
            regex=L2_NADIR_PATTERN,
            fields=[
                FileNameFieldInteger(
                    "cycle_number", description=DESCRIPTIONS["cycle_number"]
                ),
                FileNameFieldInteger(
                    "pass_number", description=DESCRIPTIONS["pass_number"]
                ),
                FileNameFieldPeriod(
                    "time", "%Y%m%d_%H%M%S", "_", description=DESCRIPTIONS["time"]
                ),
            ],
        )


class BasicNetcdfFilesDatabaseL2Nadir(FilesDatabase, PeriodMixin):
    """Database mapping to select and read L2 nadir Netcdf files in a local
    file system."""

    parser = FileNameConventionL2Nadir()
    reader = OpenMfDataset(XARRAY_TEMPORAL_NETCDFS)
    sort_keys = "time"


try:
    from fcollections.implementations.optional import (
        GeoOpenMfDataset,
        TemporalSerieAreaSelector,
    )

    class NetcdfFilesDatabaseL2Nadir(BasicNetcdfFilesDatabaseL2Nadir):
        reader = GeoOpenMfDataset(
            area_selector=TemporalSerieAreaSelector(),
            xarray_options=XARRAY_TEMPORAL_NETCDFS,
        )

except ImportError:
    import logging

    from ._definitions import MISSING_OPTIONAL_DEPENDENCIES_MESSAGE

    logger = logging.getLogger(__name__)
    logger.info(MISSING_OPTIONAL_DEPENDENCIES_MESSAGE)

    NetcdfFilesDatabaseL2Nadir = BasicNetcdfFilesDatabaseL2Nadir
