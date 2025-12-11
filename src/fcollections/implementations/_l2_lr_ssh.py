from __future__ import annotations

import re
from copy import copy

from fcollections.core import (
    Deduplicator,
    FileNameConvention,
    FileNameFieldEnum,
    FileNameFieldInteger,
    FileNameFieldPeriod,
    FilesDatabase,
    Layout,
    PeriodMixin,
    SubsetsUnmixer,
)

from ._conventions import DESCRIPTIONS
from ._definitions import (
    ProductLevel,
)
from ._products import L2VersionField, ProductSubset
from ._readers import SwotReaderL2LRSSH

SWOT_L2_PATTERN = re.compile(
    r"SWOT_(?P<level>.*)_LR_SSH_(?P<subset>.*)_(?P<cycle_number>\d{3})_(?P<pass_number>\d{3})_"
    r"(?P<time>\d{8}T\d{6}_\d{8}T\d{6})_(?P<version>P[I|G][A-Z]\d{1}_\d{2}).nc"
)


class FileNameConventionSwotL2(FileNameConvention):
    """Swot LR L2 datafiles parser."""

    def __init__(self):
        super().__init__(
            regex=SWOT_L2_PATTERN,
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
                    "level", ProductLevel, description=DESCRIPTIONS["level"]
                ),
                FileNameFieldEnum(
                    "subset", ProductSubset, description=DESCRIPTIONS["subset"]
                ),
                L2VersionField("version"),
            ],
            generation_string="SWOT_{level!f}_LR_SSH_{subset!f}_{cycle_number:>03d}_{pass_number:>03d}_{time!f}_{version!f}.nc",
        )


class _NetcdfFilesDatabaseSwotLRL2(FilesDatabase, PeriodMixin):
    """Database mapping to select and read Swot LR L2 Netcdf files in a local
    file system.

    Attributes
    ----------
    path: str
        path to a directory containing NetCDF files
    """

    parser = FileNameConventionSwotL2()
    reader = SwotReaderL2LRSSH()
    sort_keys = "time"

    # These keys determines an homogeneous subset
    unmixer = SubsetsUnmixer(partition_keys=["level", "subset"])
    # We expect multiple versions in an homogeneous subset. Only one half orbit
    # record is tolerated so we deduplicate the multiple version with an
    # autopick
    deduplicator = Deduplicator(
        unique=("cycle_number", "pass_number"), auto_pick_last=("version",)
    )


# In filenames, the version PID0_01 contains the crid and the product counter.
# In the layout, only the crid PID0 is present. When giving a reference, the
# user may give a product counter for filtering. This product counter should be
# ignored when testing occurs in the layout, else nothing will match this
# reference.
_ADAPTED_L2_FIELD: L2VersionField = copy(
    FileNameConventionSwotL2().get_field("version")
)
_ADAPTED_L2_FIELD.ignore_product_counter = True

AVISO_L2_LR_SSH_LAYOUT = Layout(
    [
        FileNameConvention(
            re.compile(r"(?P<version>P[I|G][A-Z]\d{1})"),
            [_ADAPTED_L2_FIELD],
            "{version!f}",
        ),
        FileNameConvention(
            re.compile(r"(?P<subset>.*)"),
            [FileNameConventionSwotL2().get_field("subset")],
            "{subset}",
        ),
        FileNameConvention(
            re.compile(r"cycle_(?P<cycle_number>\d{3})"),
            [FileNameConventionSwotL2().get_field("cycle_number")],
            "cycle_{cycle_number:0>3d}",
        ),
    ]
)
