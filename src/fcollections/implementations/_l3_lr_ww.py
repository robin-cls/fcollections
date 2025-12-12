from __future__ import annotations

import re

from fcollections.core import (
    FileNameConvention,
    FileNameFieldEnum,
    FileNameFieldInteger,
    FileNameFieldPeriod,
    FileNameFieldString,
    FilesDatabase,
    PeriodMixin,
    SubsetsUnmixer,
)

from ._definitions import DESCRIPTIONS, ProductSubset
from ._readers import SwotReaderL3WW

SWOT_L3_LR_WINDWAVE_PATTERN = re.compile(
    r"SWOT_L3_LR_WIND_WAVE_(?P<subset>Extended){0,1}(_){0,1}(?P<cycle_number>\d{3})_(?P<pass_number>\d{3})_"
    r"(?P<time>\d{8}T\d{6}_\d{8}T\d{6})_v(?P<version>.*).nc"
)


class FileNameConventionSwotL3WW(FileNameConvention):
    """Swot L3_LR_WIND_WAVE product file names convention."""

    def __init__(self):
        super().__init__(
            regex=SWOT_L3_LR_WINDWAVE_PATTERN,
            fields=[
                FileNameFieldInteger(
                    "cycle_number", description=DESCRIPTIONS["cycle_number"]
                ),
                FileNameFieldInteger(
                    "pass_number", description=DESCRIPTIONS["pass_number"]
                ),
                FileNameFieldPeriod(
                    "time", "%Y%m%dT%H%M%S", "_", description=DESCRIPTIONS["time"]
                ),
                FileNameFieldEnum(
                    "subset",
                    ProductSubset,
                    default=ProductSubset.Light,
                    description=DESCRIPTIONS["subset"],
                ),
                FileNameFieldString("version", description=DESCRIPTIONS["version"]),
            ],
            generation_string="SWOT_L3_LR_WIND_WAVE_{subset!f}_{cycle_number:>03d}_{pass_number:>03d}_{time!f}_v{version}.nc",
        )


class _NetcdfFilesDatabaseSwotLRWW(FilesDatabase, PeriodMixin):
    """Database mapping to explore and read the L3_LR_WIND_WAVE product.

    Attributes
    ----------
    path
        path to a directory containing the NetCDF files
    fs
        File system hosting the files. Can be used to access local or remote
        (S3, FTP, ...) file systems. Underlying readers may not be compatible
        with all file systems implementations
    layout
        Layout of the subfolders. Useful to extract information and have an
        efficient file system scanning. The recommended layout can mismatch the
        current files organization, in which case the user can build its own or
        set this parameter to None

    See Also
    --------
    fcollections.implementations.AVISO_L3_LR_WINDWAVE_LAYOUT
        Recommended layout for the database
    """

    parser = FileNameConventionSwotL3WW()
    reader = SwotReaderL3WW()
    sort_keys = "time"

    # These keys determines an homogeneous subset. We expect no duplicates in
    # an homogeneous subset
    unmixer = SubsetsUnmixer(
        partition_keys=["version", "subset"], auto_pick_last=("version",)
    )


try:
    from fcollections.implementations.optional import (
        GeoSwotReaderL3WW,
        SwotGeometryPredicate,
    )

    class NetcdfFilesDatabaseSwotLRWW(_NetcdfFilesDatabaseSwotLRWW):
        reader = GeoSwotReaderL3WW()
        predicate_classes = [SwotGeometryPredicate]

    NetcdfFilesDatabaseSwotLRWW.__doc__ = _NetcdfFilesDatabaseSwotLRWW.__doc__

except ImportError:
    import warnings

    from ._definitions import MISSING_OPTIONAL_DEPENDENCIES_MESSAGE

    warnings.warn(MISSING_OPTIONAL_DEPENDENCIES_MESSAGE)
    NetcdfFilesDatabaseSwotLRWW = _NetcdfFilesDatabaseSwotLRWW
