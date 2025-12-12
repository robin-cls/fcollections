from __future__ import annotations

import re

from fcollections.core import (
    CaseType,
    FileNameConvention,
    FileNameFieldEnum,
    FileNameFieldInteger,
    FileNameFieldPeriod,
    FilesDatabase,
    OpenMfDataset,
    PeriodMixin,
)

from ._definitions import (
    DESCRIPTIONS,
    XARRAY_TEMPORAL_NETCDFS,
    AcquisitionMode,
    S1AOWIProductType,
    S1AOWISlicePostProcessing,
)

S1AOWI_PATTERN = re.compile(
    r"s1a-(?P<acquisition_mode>.*)-owi-(?P<slice_post_processing>.*)-(?P<time>\d{8}t\d{6}-\d{8}t\d{6})-(?P<resolution>\d{6})-(?P<orbit>\d{6})_(?P<product_type>.*).nc"
)


class FileNameConventionS1AOWI(FileNameConvention):

    def __init__(self):
        super().__init__(
            regex=S1AOWI_PATTERN,
            fields=[
                FileNameFieldEnum(
                    "acquisition_mode",
                    AcquisitionMode,
                    case_type_decoded=CaseType.upper,
                    case_type_encoded=CaseType.lower,
                    description=("Acquisition mode."),
                ),
                FileNameFieldEnum(
                    "slice_post_processing",
                    S1AOWISlicePostProcessing,
                    case_type_decoded=CaseType.upper,
                    case_type_encoded=CaseType.lower,
                    description=("Slices post-processing."),
                ),
                FileNameFieldPeriod(
                    "time", "%Y%m%dt%H%M%S", "-", description=DESCRIPTIONS["time"]
                ),
                FileNameFieldInteger(
                    "resolution",
                    description=("SAR Ocean surface wind Level-2 product resolution."),
                ),
                FileNameFieldInteger("orbit", description=("Orbit number")),
                FileNameFieldEnum(
                    "product_type",
                    S1AOWIProductType,
                    case_type_decoded=CaseType.upper,
                    case_type_encoded=CaseType.lower,
                    description=("Product type."),
                ),
            ],
            generation_string="s1a-{acquisition_mode!f}-owi-{slice_post_processing!f}-{time!f}-{resolution:>06d}-{orbit:>06d}_{product_type!f}.nc",
        )


class NetcdfFilesDatabaseS1AOWI(FilesDatabase, PeriodMixin):
    """Database mapping to select and read S1A Ocean surface wind product
    Netcdf files in a local file system."""

    parser = FileNameConventionS1AOWI()
    reader = OpenMfDataset(xarray_options=XARRAY_TEMPORAL_NETCDFS)
    sort_keys = "time"
