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

from ._collections import _XARRAY_TEMPORAL_NETCDFS
from ._conventions import DESCRIPTIONS

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


class _NetcdfFilesDatabaseL2Nadir(FilesDatabase, PeriodMixin):
    """Database mapping to select and read L2 nadir Netcdf files in a local
    file system.

    Attributes
    ----------
    path: str
        path to a directory containing NetCDF files
    """

    parser = FileNameConventionL2Nadir()
    reader = OpenMfDataset(_XARRAY_TEMPORAL_NETCDFS)
    sort_keys = "time"
