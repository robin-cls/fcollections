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


class BasicNetcdfFilesDatabaseSST(FilesDatabase, PeriodMixin):
    """Database mapping to select and read sea surface temperature Netcdf files
    in a local file system."""

    parser = FileNameConventionSST()
    reader = OpenMfDataset(XARRAY_TEMPORAL_NETCDFS)
    sort_keys = "time"


try:
    from fcollections.implementations.optional import AreaSelector2D, GeoOpenMfDataset

    class NetcdfFilesDatabaseSST(BasicNetcdfFilesDatabaseSST):
        reader = GeoOpenMfDataset(
            area_selector=AreaSelector2D(longitude="lon", latitude="lat"),
            xarray_options=XARRAY_TEMPORAL_NETCDFS,
        )

except ImportError:
    import logging

    from ._definitions import MISSING_OPTIONAL_DEPENDENCIES_MESSAGE

    logger = logging.getLogger(__name__)
    logger.info(MISSING_OPTIONAL_DEPENDENCIES_MESSAGE)

    NetcdfFilesDatabaseSST = BasicNetcdfFilesDatabaseSST
