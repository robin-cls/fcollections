from __future__ import annotations

import re

import numpy as np

from fcollections.core import (
    CaseType,
    FileNameConvention,
    FileNameFieldDateDelta,
    FileNameFieldEnum,
    FileNameFieldString,
    FilesDatabase,
    OpenMfDataset,
    PeriodMixin,
)

from ._definitions import (
    DESCRIPTIONS,
    XARRAY_TEMPORAL_NETCDFS,
    Delay,
    OCVariable,
    ProductLevel,
    Sensor,
)

OC_PATTERN = re.compile(
    r"(?P<time>\d{8})_cmems_obs-oc_glo_bgc-(?P<oc_variable>.*)_(?P<delay>.*)_(?P<level>l3|l4)(-gapfree){0,1}-(?P<sensor>.*)-(?P<spatial_resolution>4km|1km|300m)_(?P<temporal_resolution>P1D|P1M).nc"
)


class FileNameConventionOC(FileNameConvention):
    """Ocean Color datafiles parser."""

    def __init__(self):
        super().__init__(
            regex=OC_PATTERN,
            fields=[
                FileNameFieldDateDelta(
                    "time",
                    "%Y%m%d",
                    np.timedelta64(1, "D"),
                    description=DESCRIPTIONS["time"],
                ),
                FileNameFieldEnum(
                    "oc_variable",
                    OCVariable,
                    case_type_decoded=CaseType.upper,
                    case_type_encoded=CaseType.lower,
                    description=DESCRIPTIONS["oc_variable"],
                ),
                FileNameFieldEnum(
                    "delay",
                    Delay,
                    case_type_decoded=CaseType.upper,
                    case_type_encoded=CaseType.lower,
                    description=DESCRIPTIONS["delay"],
                ),
                FileNameFieldEnum(
                    "level",
                    ProductLevel,
                    case_type_decoded=CaseType.upper,
                    case_type_encoded=CaseType.lower,
                    description=DESCRIPTIONS["level"],
                ),
                FileNameFieldEnum(
                    "sensor",
                    Sensor,
                    case_type_decoded=CaseType.upper,
                    case_type_encoded=CaseType.lower,
                    description=DESCRIPTIONS["sensor"],
                ),
                FileNameFieldString(
                    "spatial_resolution", description=DESCRIPTIONS["spatial_resolution"]
                ),
                FileNameFieldString(
                    "temporal_resolution",
                    description=DESCRIPTIONS["temporal_resolution"],
                ),
            ],
        )


class BasicNetcdfFilesDatabaseOC(FilesDatabase, PeriodMixin):
    """Database mapping to select and read ocean color Netcdf files in a local
    file system."""

    parser = FileNameConventionOC()
    reader = OpenMfDataset(XARRAY_TEMPORAL_NETCDFS)
    sort_keys = "time"


try:
    from fcollections.implementations.optional import AreaSelector2D, GeoOpenMfDataset

    class NetcdfFilesDatabaseOC(BasicNetcdfFilesDatabaseOC):
        reader = GeoOpenMfDataset(
            area_selector=AreaSelector2D(longitude="lon", latitude="lat"),
            xarray_options=XARRAY_TEMPORAL_NETCDFS,
        )

except ImportError:
    import logging

    from ._definitions import MISSING_OPTIONAL_DEPENDENCIES_MESSAGE

    logger = logging.getLogger(__name__)
    logger.info(MISSING_OPTIONAL_DEPENDENCIES_MESSAGE)

    NetcdfFilesDatabaseOC = BasicNetcdfFilesDatabaseOC
