from __future__ import annotations

import re
from copy import copy

from fcollections.core import (
    FileNameConvention,
    FileNameFieldDatetime,
    FileNameFieldPeriod,
    FilesDatabase,
    Layout,
    OpenMfDataset,
    PeriodMixin,
)
from fcollections.implementations._definitions._cmems import (
    _FIELDS,
    build_convention,
    build_layout,
)

from ._definitions import DESCRIPTIONS, XARRAY_TEMPORAL_NETCDFS

_SENSOR_FIELD = _FIELDS[-1]

SWH_PATTERN = re.compile(
    rf"global_vavh_l3_rt_(?P<sensorf>{'|'.join(_SENSOR_FIELD.choices())})_(?P<time>\d{{8}}T\d{{6}}_\d{{8}}T\d{{6}})_(?P<production_date>\d{{8}}T\d{{6}}).nc"
)

# Sensor names in dataset and file are not the same for s6a/s6a_hr and swon/swot
# Need to distinguish both field to account for this particularity
_SENSOR_FIELD_FILENAME = copy(_SENSOR_FIELD)
_SENSOR_FIELD_FILENAME.name = "sensorf"


class FileNameConventionSWH(FileNameConvention):

    def __init__(self):
        super().__init__(
            regex=SWH_PATTERN,
            fields=[
                _SENSOR_FIELD_FILENAME,
                FileNameFieldPeriod(
                    "time", "%Y%m%dT%H%M%S", "_", description=DESCRIPTIONS["time"]
                ),
                FileNameFieldDatetime(
                    "production_date",
                    "%Y%m%dT%H%M%S",
                    description=DESCRIPTIONS["production_date"],
                ),
            ],
            generation_string="global_vavh_l3_rt_{sensorf!f}_{time!f}_{production_date!f}.nc",
        )


CMEMS_SWH_LAYOUT = build_layout(
    build_convention(
        complementary=f"(?P<sensor>{'|'.join(_SENSOR_FIELD.choices())})-l3",
        complementary_fields=[_SENSOR_FIELD],
        complementary_generation_string="{sensor!f}-l3",
    ),
    FileNameConventionSWH(),
)


class BasicNetcdfFilesDatabaseSWH(FilesDatabase, PeriodMixin):
    """Database mapping to select and read significant wave height Netcdf files
    in a local file system."""

    layouts = [CMEMS_SWH_LAYOUT, Layout([FileNameConventionSWH()])]
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
