from __future__ import annotations

import re
from copy import copy

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
    Layout,
    OpenMfDataset,
    PeriodMixin,
    SubsetsUnmixer,
)

from ._definitions._cmems import (
    CMEMS_DATASET_ID_FIELDS,
    build_convention,
    build_layout,
)
from ._definitions._constants import (
    DESCRIPTIONS,
    XARRAY_TEMPORAL_NETCDFS,
    Delay,
    ProductLevel,
)

# The sensor is actually composed of the mission name and optionally the orbit
# or the instrument mode (j3, j3n, s6a-lr). When the instrument mode is given,
# it is separated from the mission name with '_' for the file names (s6a_hr)
# and '-' for the folder name (s6a-hr).
# By default, the sensor field name uses '-' for encoded string. Needs to adapt
# the behavior to keep the '_' in the encoded string
_SENSOR_FIELD: FileNameFieldEnum = CMEMS_DATASET_ID_FIELDS[-1]
_SENSOR_FIELD_FILENAME = copy(_SENSOR_FIELD)
_SENSOR_FIELD_FILENAME.underscore_encoded = True


L3_NADIR_PATTERN = re.compile(
    rf"(?P<delay>nrt|dt)_global_(?P<sensor>{'|'.join(_SENSOR_FIELD_FILENAME.choices())})_(hr_){{0,1}}phy_(aux_){{0,1}}(?P<product_level>l3)_(?P<resolution>\d+)*(hz_)*(?P<time>\d{{8}})_(?P<production_date>\d{{8}}).nc"
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
                _SENSOR_FIELD_FILENAME,
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
            generation_string="{delay!f}_global_{sensor!f}_phy_{product_level!f}_{resolution!f}hz_{time!f}_{production_date!f}",
        )


_DATASET_ID_CONVENTION = build_convention(
    complementary=f"(?P<sensor>{'|'.join(_SENSOR_FIELD.choices())})-l3-duacs",
    complementary_fields=[_SENSOR_FIELD],
    complementary_generation_string="{sensor!f}-l3-duacs",
)

CMEMS_SSHA_L3_LAYOUT = build_layout(_DATASET_ID_CONVENTION, FileNameConventionL3Nadir())


class BasicNetcdfFilesDatabaseL3Nadir(FilesDatabase, PeriodMixin):
    """Database mapping to select and read L3 nadir Netcdf files in a local
    file system."""

    layouts = [CMEMS_SSHA_L3_LAYOUT, Layout([FileNameConventionL3Nadir()])]
    deduplicator = Deduplicator(unique=("time",), auto_pick_last=("production_date",))
    unmixer = SubsetsUnmixer(partition_keys=["sensor", "resolution"])
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

    from ._definitions._constants import MISSING_OPTIONAL_DEPENDENCIES_MESSAGE

    logger = logging.getLogger(__name__)
    logger.info(MISSING_OPTIONAL_DEPENDENCIES_MESSAGE)

    NetcdfFilesDatabaseL3Nadir = BasicNetcdfFilesDatabaseL3Nadir
