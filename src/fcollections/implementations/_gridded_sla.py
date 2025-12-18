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
    r"(?P<delay>nrt|dt)_(.*)_allsat_phy_l4_(?P<time>(\d{8})|(\d{8}T\d{2}))_(?P<production_date>\d{8}).nc"
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
            generation_string="{delay!f}_global_allsat_phy_l4_{time!f}_{production_date!f}.nc",
        )


AVISO_L4_SWOT_LAYOUT = Layout(
    [
        FileNameConvention(
            re.compile(r"^v(?P<version>.*)$"),
            [FileNameFieldString("version")],
            "v{version!f}",
        ),
        FileNameConvention(
            re.compile(r"^(?P<method>4dvarnet|4dvarqg|miost)$"),
            [FileNameFieldString("method")],
            "{method}",
        ),
        FileNameConvention(
            re.compile(r"^(?P<phase>calval|science)$"),
            [FileNameFieldEnum("phase", MissionsPhases)],
            "{phase!f}",
        ),
        FileNameConventionGriddedSLA(),
    ]
)

CMEMS_L4_SSHA_LAYOUT = Layout(
    [
        FileNameConvention(
            re.compile(
                r"^cmems_obs-sl_glo_phy-ssh_(?P<delay_nrt_my>nrt|my)_allsat-l4-duacs-(?P<spatial_resolution>.*)deg_P(?P<temporal_resolution>.*)D_(?P<version>\d{6})"
            ),
            [
                FileNameFieldEnum(
                    "delay_nrt_my",
                    Delay,
                    case_type_decoded=CaseType.upper,
                    case_type_encoded=CaseType.lower,
                    description=DESCRIPTIONS["delay"],
                ),
                FileNameFieldFloat("spatial_resolution"),
                FileNameFieldFloat("temporal_resolution"),
                FileNameFieldString("version"),
            ],
            "cmems_obs-sl_glo_phy-ssh_{delay_nrt_my!f}_allsat-l4-duacs-{spatial_resolution!f}deg_P{temporal_resolution!f}D_{version}",
        ),
        FileNameConvention(
            re.compile(r"^(?P<year>\d{4})$"),
            [FileNameFieldInteger("year")],
            "{year!f}",
        ),
        FileNameConvention(
            re.compile(r"^(?P<month>\d{2})$"),
            [FileNameFieldInteger("month")],
            "{month:>02d}",
        ),
        FileNameConventionGriddedSLA(),
    ]
)


class BasicNetcdfFilesDatabaseGriddedSLA(FilesDatabase, PeriodMixin):
    """Database mapping to select and read gridded Sla Netcdf files in a local
    file system."""

    layouts = [
        Layout([FileNameConventionGriddedSLA()]),
        AVISO_L4_SWOT_LAYOUT,
        CMEMS_L4_SSHA_LAYOUT,
    ]
    reader = OpenMfDataset(XARRAY_TEMPORAL_NETCDFS)
    sort_keys = "time"


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
