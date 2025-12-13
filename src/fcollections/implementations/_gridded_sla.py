from __future__ import annotations

import re

import numpy as np

from fcollections.core import (
    CaseType,
    FileNameConvention,
    FileNameFieldDateDelta,
    FileNameFieldDateJulianDelta,
    FileNameFieldDatetime,
    FileNameFieldEnum,
    FileNameFieldFloat,
    FileNameFieldInteger,
    FileNameFieldString,
    FilesDatabase,
    Layout,
    OpenMfDataset,
    PeriodMixin,
)
from fcollections.missions import MissionsPhases

from ._definitions import DESCRIPTIONS, XARRAY_TEMPORAL_NETCDFS, Delay

GRIDDED_SLA_PATTERN = re.compile(
    r"(?P<delay>.*)_(.*)_allsat_phy_l4_(?P<time>(\d{8})|(\d{8}T\d{2}))_(?P<production_date>\d{8}).nc"
)

INTERNAL_SLA_PATTERN = re.compile(r"msla_oer_merged_h_(?P<date>\d{5}).nc")


class FileNameConventionGriddedSLA(FileNameConvention):
    """Gridded SLA datafiles parser."""

    def __init__(self):
        super().__init__(
            regex=GRIDDED_SLA_PATTERN,
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
                    ["%Y%m%d", "%Y%m%dT%H"],
                    np.timedelta64(1, "D"),
                    description=DESCRIPTIONS["time"],
                ),
                FileNameFieldDatetime(
                    "production_date",
                    "%Y%m%d",
                    description=DESCRIPTIONS["production_date"],
                ),
            ],
        )


class BasicNetcdfFilesDatabaseGriddedSLA(FilesDatabase, PeriodMixin):
    """Database mapping to select and read gridded Sla Netcdf files in a local
    file system."""

    parser = FileNameConventionGriddedSLA()
    reader = OpenMfDataset(XARRAY_TEMPORAL_NETCDFS)
    sort_keys = "time"


class _FileNameFieldIntegerAdapter(FileNameFieldInteger):
    """Specific field for sampling definition in file versus folder names.

    In folder names, a sampling of 5Hz is given as PT0.2S, whereas it is
    given as 5Hz in the file name. This field converts PT0.2S -> 5 to
    have the same folder and file fields.
    """

    def decode(self, input_string: str) -> int:
        f = FileNameFieldFloat("dummy")
        return int(1 / f.decode(input_string))

    def encode(self, data: int) -> str:
        invert = 1 / data
        return str(invert) if invert % 1 != 0 else str(int(invert))


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


CMEMS_NADIR_SSHA_LAYOUT = Layout(
    [
        FileNameConvention(
            re.compile(
                r"cmems_obs-sl_glo_phy-ssh_(?P<delay>nrt|my)_(?P<mission>.*)-l3-duacs_PT(?P<resolution>.*)S(-i){0,1}_(?P<version>.*)"
            ),
            [
                FileNameFieldEnum(
                    "delay",
                    Delay,
                    case_type_decoded=CaseType.upper,
                    case_type_encoded=CaseType.lower,
                ),
                _FileNameFieldEnumAdapter("mission", MissionsPhases),
                _FileNameFieldIntegerAdapter("resolution"),
                FileNameFieldString("version"),
            ],
            "cmems_obs-sl_glo_phy-ssh_{delay!f}_{mission!f}-l3-duacs_PT{resolution!f}S_{version}",
        ),
        FileNameConvention(
            re.compile(r"(?P<year>\d{4})"), [FileNameFieldInteger("year")], "{year}"
        ),
        FileNameConvention(
            re.compile(r"(?P<month>\d{2})"),
            [FileNameFieldInteger("month")],
            "{month:0>2d}",
        ),
    ]
)


class FileNameConventionGriddedSLAInternal(FileNameConvention):

    def __init__(self):
        super().__init__(
            regex=INTERNAL_SLA_PATTERN,
            fields=[
                FileNameFieldDateJulianDelta(
                    "date",
                    reference=np.datetime64("1950-01-01T00"),
                    delta=np.timedelta64(1, "D"),
                    description=DESCRIPTIONS["time"],
                )
            ],
            generation_string="msla_oer_merged_h_{date!f}.nc",
        )


AVISO_L4_SWOT_LAYOUT = Layout(
    [
        FileNameConvention(
            re.compile(r"v(?P<version>.*)"),
            [FileNameFieldString("version")],
            "v{version!f}",
        ),
        FileNameConvention(
            re.compile(r"(?P<method>4dvarnet|4dvarqg|miost)"),
            [FileNameFieldString("method")],
            "{method}",
        ),
        FileNameConvention(
            re.compile(r"(?P<phase>.*)"),
            [FileNameFieldEnum("phase", MissionsPhases)],
            "{phase!f}",
        ),
    ]
)


try:
    from fcollections.implementations.optional import AreaSelector2D, GeoOpenMfDataset

    class NetcdfFilesDatabaseGriddedSLA(BasicNetcdfFilesDatabaseGriddedSLA):
        reader = GeoOpenMfDataset(
            area_selector=AreaSelector2D(), xarray_options=XARRAY_TEMPORAL_NETCDFS
        )

except ImportError:
    import logging

    from ._definitions import MISSING_OPTIONAL_DEPENDENCIES_MESSAGE

    logger = logging.getLogger(__name__)
    logger.info(MISSING_OPTIONAL_DEPENDENCIES_MESSAGE)

    NetcdfFilesDatabaseGriddedSLA = BasicNetcdfFilesDatabaseGriddedSLA
