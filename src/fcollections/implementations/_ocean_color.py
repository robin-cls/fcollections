from __future__ import annotations

import re

import numpy as np

from fcollections.core import (
    FileNameConvention,
    FileNameFieldDateDelta,
    FileNameFieldString,
    FilesDatabase,
    Layout,
    OpenMfDataset,
    PeriodMixin,
)

from ._definitions._cmems import (
    _FIELDS,
    build_convention,
    build_layout,
)
from ._definitions._constants import DESCRIPTIONS, XARRAY_TEMPORAL_NETCDFS

_COMPLEMENTARY_INFO = [
    f"(?P<level>l3|l4|l4-gapfree)-(?P<sensor>{'|'.join(_FIELDS[-1].choices())})(-climatology){{0,1}}-(?P<spatial_resolution>\\d+(km|m))",
    [
        FileNameFieldString("level", description=DESCRIPTIONS["level"]),
        _FIELDS[-1],
        FileNameFieldString(
            "spatial_resolution", description=DESCRIPTIONS["spatial_resolution"]
        ),
    ],
    "{level}-{sensor!f}-{spatial_resolution!f}",
]

_DATASET_ID_CONVENTION = build_convention(*_COMPLEMENTARY_INFO, strict=False)

# The filename convention simply extends the dataset id convention
OC_PATTERN = re.compile(rf"(?P<time>\d{{8}})_{_DATASET_ID_CONVENTION.regex.pattern}.nc")


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
                *_DATASET_ID_CONVENTION.fields,
            ],
        )


CMEMS_OC_LAYOUT = build_layout(
    # Need strict convention to avoid parsing a file node at folder level
    build_convention(*_COMPLEMENTARY_INFO, strict=True),
    FileNameConventionOC(),
)


class BasicNetcdfFilesDatabaseOC(FilesDatabase, PeriodMixin):
    """Database mapping to select and read ocean color Netcdf files in a local
    file system."""

    layouts = [CMEMS_OC_LAYOUT, Layout([FileNameConventionOC()])]
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

    from ._definitions._constants import MISSING_OPTIONAL_DEPENDENCIES_MESSAGE

    logger = logging.getLogger(__name__)
    logger.info(MISSING_OPTIONAL_DEPENDENCIES_MESSAGE)

    NetcdfFilesDatabaseOC = BasicNetcdfFilesDatabaseOC
