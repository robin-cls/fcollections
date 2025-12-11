import re

from fcollections.core import (
    FileNameConvention,
    FileNameFieldDatetime,
    FilesDatabase,
    OpenMfDataset,
    PeriodMixin,
)

from ._definitions import DESCRIPTIONS, XARRAY_TEMPORAL_NETCDFS

SST_PATTERN = re.compile(
    r"(?P<time>\d{8}\d{6})-IFR-L3S_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v02.1-fv01.0.nc"
)


class FileNameConventionSST(FileNameConvention):
    """Sea Surface Temperature datafiles parser."""

    def __init__(self):
        super().__init__(
            regex=SST_PATTERN,
            fields=[
                FileNameFieldDatetime(
                    "time", "%Y%m%d%H%M%S", description=DESCRIPTIONS["time"]
                )
            ],
            generation_string="{time!f}-IFR-L3S_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v02.1-fv01.0.nc",
        )


class _NetcdfFilesDatabaseSST(FilesDatabase, PeriodMixin):
    """Database mapping to select and read sea surface temperature Netcdf files
    in a local file system.

    Attributes
    ----------
    path: str
        path to directory containing NetCDF files
    """

    parser = FileNameConventionSST()
    reader = OpenMfDataset(XARRAY_TEMPORAL_NETCDFS)
    sort_keys = "time"
