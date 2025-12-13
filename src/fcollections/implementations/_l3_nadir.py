from __future__ import annotations

import re
from typing import TYPE_CHECKING

import numpy as np

from fcollections.core import (
    CaseType,
    Deduplicator,
    FileNameConvention,
    FileNameFieldDateDelta,
    FileNameFieldDatetime,
    FileNameFieldEnum,
    FileNameFieldInteger,
    FilesDatabase,
    OpenMfDataset,
    PeriodMixin,
    SubsetsUnmixer,
)
from fcollections.missions import MissionsPhases

from ._definitions import DESCRIPTIONS, XARRAY_TEMPORAL_NETCDFS, Delay, ProductLevel

if TYPE_CHECKING:
    from pathlib import Path


L3_NADIR_PATTERN = re.compile(
    r"(?P<delay>.*)_global_(?P<mission>.*)_(hr_){0,1}phy_(aux_){0,1}(?P<product_level>l3)_(?P<resolution>\d+)*(hz_)*(?P<time>\d{8})_(?P<production_date>\d{8}).nc"
)


class FileNameConventionL3Nadir(FileNameConvention):
    """L3 Nadir datafiles parser."""

    def __init__(self):
        super().__init__(
            regex=L3_NADIR_PATTERN,
            fields=[
                FileNameFieldEnum(
                    "delay",
                    Delay,
                    case_type_decoded=CaseType.upper,
                    case_type_encoded=CaseType.lower,
                    description=DESCRIPTIONS["delay"],
                ),
                FileNameFieldDateDelta(
                    "time",
                    "%Y%m%d",
                    np.timedelta64(1, "D"),
                    description=DESCRIPTIONS["time"],
                ),
                FileNameFieldDatetime(
                    "production_date",
                    "%Y%m%d",
                    description=(
                        "Production date of a given file. The same granule is "
                        "regenerated multiple times with updated corrections. Hence"
                        " there can be multiple files for the same period, but with"
                        " a different production date."
                    ),
                ),
                FileNameFieldEnum(
                    "mission",
                    MissionsPhases,
                    description=("Altimetry mission in the file."),
                ),
                FileNameFieldEnum(
                    "product_level",
                    ProductLevel,
                    "upper",
                    description="Product level of the data.",
                ),
                FileNameFieldInteger(
                    "resolution",
                    default=1,
                    description=(
                        "Data resolution. Nadir products may be sampled at 1Hz, 5Hz"
                        " or 20Hz depending on the level and dataset considered."
                    ),
                ),
            ],
        )


class BasicNetcdfFilesDatabaseL3Nadir(FilesDatabase, PeriodMixin):
    """Database mapping to select and read L3 nadir Netcdf files in a local
    file system."""

    parser = FileNameConventionL3Nadir()
    deduplicator = Deduplicator(unique=("time",), auto_pick_last=("production_date",))
    unmixer = SubsetsUnmixer(partition_keys=["mission", "resolution"])
    reader = OpenMfDataset(XARRAY_TEMPORAL_NETCDFS)
    sort_keys = "time"


try:
    from fcollections.implementations.optional import (
        GeoOpenMfDataset,
        TemporalSerieAreaSelector,
    )

    class NetcdfFilesDatabaseL3Nadir(BasicNetcdfFilesDatabaseL3Nadir):
        reader = GeoOpenMfDataset(
            area_selector=TemporalSerieAreaSelector(),
            xarray_options=XARRAY_TEMPORAL_NETCDFS,
        )

except ImportError:
    import logging

    from ._definitions import MISSING_OPTIONAL_DEPENDENCIES_MESSAGE

    logger = logging.getLogger(__name__)
    logger.info(MISSING_OPTIONAL_DEPENDENCIES_MESSAGE)

    NetcdfFilesDatabaseL3Nadir = BasicNetcdfFilesDatabaseL3Nadir
