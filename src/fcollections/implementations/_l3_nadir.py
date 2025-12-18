from __future__ import annotations

import re

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
from fcollections.missions import MissionsPhases

from ._definitions import (
    DESCRIPTIONS,
    XARRAY_TEMPORAL_NETCDFS,
    Delay,
    ProductLevel,
    build_convention,
    build_layout,
)

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
            generation_string="{delay!f}_global_{mission!f}_phy_{product_level!f}_{resolution!f}hz_{time!f}_{production_date!f}",
        )


class _FileNameFieldEnumAdapter(FileNameFieldEnum):
    """Missions names in CMEMS folder versus file names differ.

    The mission is actually composed of the mission name and optionally the
    orbit or the instrument mode (j3, j3n, s6a-lr). When the instrument mode is
    given, it is separated from the mission name with '_' for the file names
    (s6a_hr) and '-' for the folder name (s6a-hr).

    By default, the mission name uses '_' in MissionsPhases. This enum adapts
    the encoding/decoding of the folder name.

    See Also
    --------
    fcollections.core.missions.MissionsPhases: mission phases definitions
    """

    def decode(self, input_string: str) -> MissionsPhases:
        return super().decode(input_string.replace("-", "_"))

    def encode(self, data: MissionsPhases) -> str:
        return super().encode(data).replace("_", "-")


_enum_field = _FileNameFieldEnumAdapter("mission", MissionsPhases)

_DATASET_ID_CONVENTION = build_convention(
    complementary=f"(?P<mission>{'|'.join(_enum_field.choices())})-l3-duacs",
    complementary_fields=[_enum_field],
    complementary_generation_string="{mission!f}-l3-duacs",
)

CMEMS_SSHA_L3_LAYOUT = build_layout(_DATASET_ID_CONVENTION, FileNameConventionL3Nadir())


class BasicNetcdfFilesDatabaseL3Nadir(FilesDatabase, PeriodMixin):
    """Database mapping to select and read L3 nadir Netcdf files in a local
    file system."""

    layouts = [CMEMS_SSHA_L3_LAYOUT, Layout([FileNameConventionL3Nadir()])]
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
