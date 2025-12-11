from __future__ import annotations

import re
from copy import copy

import numpy as np

from fcollections.core import (
    CaseType,
    CompositeLayout,
    FileNameConvention,
    FileNameFieldDateDelta,
    FileNameFieldDateJulian,
    FileNameFieldDateJulianDelta,
    FileNameFieldDatetime,
    FileNameFieldEnum,
    FileNameFieldFloat,
    FileNameFieldInteger,
    FileNameFieldPeriod,
    FileNameFieldString,
    Layout,
)
from fcollections.missions import MissionsPhases

from ._definitions import (
    AcquisitionMode,
    Delay,
    OCVariable,
    ProductLevel,
    S1AOWIProductType,
    S1AOWISlicePostProcessing,
    Sensor,
    Temporality,
)
from ._products import L2VersionField, ProductSubset

# This pattern is used for Swot data preprocessing
SWOT_PATTERN = re.compile(r"(.*)_(?P<cycle_number>\d{3})_(?P<pass_number>\d{3})_(.*)")

SWOT_L2_PATTERN = re.compile(
    r"SWOT_(?P<level>.*)_LR_SSH_(?P<subset>.*)_(?P<cycle_number>\d{3})_(?P<pass_number>\d{3})_"
    r"(?P<time>\d{8}T\d{6}_\d{8}T\d{6})_(?P<version>P[I|G][A-Z]\d{1}_\d{2}).nc"
)

SWOT_L3_PATTERN = re.compile(
    r"SWOT_(?P<level>.*)_LR_SSH_(?P<subset>.*)_(?P<cycle_number>\d{3})_(?P<pass_number>\d{3})_"
    r"(?P<time>\d{8}T\d{6}_\d{8}T\d{6})_v(?P<version>.*).nc"
)

SWOT_L3_LR_WINDWAVE_PATTERN = re.compile(
    r"SWOT_L3_LR_WIND_WAVE_(?P<subset>Extended){0,1}(_){0,1}(?P<cycle_number>\d{3})_(?P<pass_number>\d{3})_"
    r"(?P<time>\d{8}T\d{6}_\d{8}T\d{6})_v(?P<version>.*).nc"
)

OC_PATTERN = re.compile(
    r"(?P<time>\d{8})_cmems_obs-oc_glo_bgc-(?P<oc_variable>.*)_(?P<delay>.*)_(?P<level>l3|l4)(-gapfree){0,1}-(?P<sensor>.*)-(?P<spatial_resolution>4km|1km|300m)_(?P<temporal_resolution>P1D|P1M).nc"
)

GRIDDED_SLA_PATTERN = re.compile(
    r"(?P<delay>.*)_(.*)_allsat_phy_l4_(?P<time>(\d{8})|(\d{8}T\d{2}))_(?P<production_date>\d{8}).nc"
)

INTERNAL_SLA_PATTERN = re.compile(r"msla_oer_merged_h_(?P<date>\d{5}).nc")

DAC_PATTERN = re.compile(r"dac_dif_((\d+)days_){0,1}(?P<time>\d{5}_\d{2}).nc")

OHC_PATTERN = re.compile(
    r"OHC-NAQG3_v(.*)r(.*)_blend_s(.*)_e(.*)_c(?P<time>\d{8})(.*).nc"
)

SWH_PATTERN = re.compile(
    r"global_vavh_l3_rt_(?P<mission>.*)_(?P<time>\d{8}T\d{6}_\d{8}T\d{6})_(?P<production_date>\d{8}T\d{6}).nc"
)

S1AOWI_PATTERN = re.compile(
    r"s1a-(?P<acquisition_mode>.*)-owi-(?P<slice_post_processing>.*)-(?P<time>\d{8}t\d{6}-\d{8}t\d{6})-(?P<resolution>\d{6})-(?P<orbit>\d{6})_(?P<product_type>.*).nc"
)

ERA5_PATTERN = re.compile(r"reanalysis-era5-single-levels_(?P<time>\d{8}).nc")

MUR_PATTERN = re.compile(
    r"(?P<time>\d{8}\d{6})-JPL-L4_GHRSST-SSTfnd-MUR-GLOB-v(.*)-fv(.*).nc"
)

L3_NADIR_PATTERN = re.compile(
    r"(?P<delay>.*)_global_(?P<mission>.*)_(hr_){0,1}phy_(aux_){0,1}(?P<product_level>l3)_(?P<resolution>\d+)*(hz_)*(?P<time>\d{8})_(?P<production_date>\d{8}).nc"
)

L2_NADIR_PATTERN = re.compile(
    r"SWOT_(GPN|IPN)_2PfP(?P<cycle_number>\d{3})_(?P<pass_number>\d{3})_(?P<time>\d{8}_\d{6}_\d{8}_\d{6}).nc"
)

DESCRIPTIONS = {
    "cycle_number": (
        "Cycle number of the half orbit. A half orbit is "
        "identified using a cycle number and a pass number."
    ),
    "pass_number": (
        "Pass number of the half orbit. A half orbit is "
        "identified using a cycle number and a pass number."
    ),
    "time": "Period covered by the file.",
    "level": "Product level of the data.",
    "subset": (
        "Subset of the LR Karin products. The Basic, Expert and Technical subsets "
        "are defined on a reference grid, opening the possibility of stacking the "
        "files, whereas the Unsmoothed subset is defined on a different grid for "
        "each cycle. The Light and Extended subset are specific to the "
        "L3_LR_WIND_WAVE product."
    ),
    "production_date": (
        "Production date of a given file. The same granule is "
        "regenerated multiple times with updated corrections. Hence"
        " there can be multiple files for the same period, but with"
        " a different production date."
    ),
    "sensor": "Sensor.",
    "delay": "Delay.",
    "oc_variable": "Ocean color variable.",
    "temporal_resolution": "Temporal resolution, such as P1D, P1M.",
    "spatial_resolution": "Spatial resolution, such as 4km, 1km, 300M.",
    "version": (
        "Version of the L3_LR_WIND_WAVE and L3_LR_SSH Swot products (they share "
        'their versioning). This is a tri-number version x.y.z, where "x" denotes '
        'a major change in the product, "y" a minor change and "z" a fix.'
    ),
}


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


class FileNameConventionSwotL3(FileNameConvention):
    """Swot LR L3 datafiles parser."""

    def __init__(self):
        super().__init__(
            regex=SWOT_L3_PATTERN,
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
                FileNameFieldString("version", description=DESCRIPTIONS["version"]),
            ],
            generation_string="SWOT_{level!f}_LR_SSH_{subset!f}_{cycle_number:>03d}_{pass_number:>03d}_{time!f}_v{version}.nc",
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
                FileNameFieldEnum(
                    "oc_variable",
                    OCVariable,
                    case_type_decoded=CaseType.upper,
                    case_type_encoded=CaseType.lower,
                    description=DESCRIPTIONS["oc_variable"],
                ),
                FileNameFieldEnum(
                    "delay",
                    Delay,
                    case_type_decoded=CaseType.upper,
                    case_type_encoded=CaseType.lower,
                    description=DESCRIPTIONS["delay"],
                ),
                FileNameFieldEnum(
                    "level",
                    ProductLevel,
                    case_type_decoded=CaseType.upper,
                    case_type_encoded=CaseType.lower,
                    description=DESCRIPTIONS["level"],
                ),
                FileNameFieldEnum(
                    "sensor",
                    Sensor,
                    case_type_decoded=CaseType.upper,
                    case_type_encoded=CaseType.lower,
                    description=DESCRIPTIONS["sensor"],
                ),
                FileNameFieldString(
                    "spatial_resolution", description=DESCRIPTIONS["spatial_resolution"]
                ),
                FileNameFieldString(
                    "temporal_resolution",
                    description=DESCRIPTIONS["temporal_resolution"],
                ),
            ],
        )


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


class FileNameConventionDAC(FileNameConvention):

    def __init__(self):
        super().__init__(
            regex=DAC_PATTERN,
            fields=[
                FileNameFieldDateJulian(
                    "time",
                    reference=np.datetime64("1950-01-01T00"),
                    julian_day_format="days_hours",
                )
            ],
            generation_string="dac_dif_{time!f}.nc",
        )


class FileNameConventionOHC(FileNameConvention):

    def __init__(self):
        super().__init__(
            regex=OHC_PATTERN,
            fields=[
                FileNameFieldDatetime(
                    "time", "%Y%m%d", description=DESCRIPTIONS["time"]
                ),
            ],
        )


class FileNameConventionSWH(FileNameConvention):

    def __init__(self):
        super().__init__(
            regex=SWH_PATTERN,
            fields=[
                FileNameFieldEnum(
                    "mission",
                    MissionsPhases,
                    description=("Altimetry mission in the file."),
                ),
                FileNameFieldPeriod(
                    "time", "%Y%m%dT%H%M%S", "_", description=DESCRIPTIONS["time"]
                ),
                FileNameFieldDatetime(
                    "production_date",
                    "%Y%m%dT%H%M%S",
                    description=DESCRIPTIONS["production_date"],
                ),
            ],
            generation_string="global_vavh_l3_rt_{mission!f}_{time!f}_{production_date!f}.nc",
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


class FileNameConventionERA5(FileNameConvention):

    def __init__(self):
        super().__init__(
            regex=ERA5_PATTERN,
            fields=[
                FileNameFieldDatetime(
                    "time", "%Y%m%d", description=DESCRIPTIONS["time"]
                )
            ],
            generation_string="reanalysis-era5-single-levels_{time!f}.nc",
        )


class FileNameConventionMUR(FileNameConvention):

    def __init__(self):
        super().__init__(
            regex=MUR_PATTERN,
            fields=[
                FileNameFieldDatetime(
                    "time", "%Y%m%d%H%M%S", description=DESCRIPTIONS["time"]
                )
            ],
            generation_string="{time!f}-JPL-L4_GHRSST-SSTfnd-MUR-GLOB-v02.0-fv04.1.nc",
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


class _FileNameFieldStringAdapter(FileNameFieldString):
    """Specific field for L3_LR_SSH version in folder versus file.

    L3_LR_SSH version is given as 1.0.0 in the files, but as 1_0_0 in
    the folder. In order to have consistent fields between the file name
    parsing and the folder layout parsing, we define this very specific
    adapter.
    """

    def decode(self, a: str) -> str:
        return super().decode(a.replace("_", "."))

    def encode(self, a: str) -> str:
        return super().encode(a.replace(".", "_"))


_AVISO_L3_LR_SSH_LAYOUT_V2 = Layout(
    [
        FileNameConvention(
            re.compile(r"v(?P<version>.*)"),
            [_FileNameFieldStringAdapter("version")],
            "v{version!f}",
        ),
        FileNameConvention(
            re.compile(r"(?P<subset>.*)"),
            [FileNameConventionSwotL3().get_field("subset")],
            "{subset}",
        ),
        FileNameConvention(
            re.compile(r"cycle_(?P<cycle_number>\d{3})"),
            [FileNameConventionSwotL3().get_field("cycle_number")],
            "cycle_{cycle_number:0>3d}",
        ),
    ]
)

_AVISO_L3_LR_SSH_LAYOUT_V3 = Layout(
    [
        *_AVISO_L3_LR_SSH_LAYOUT_V2.conventions[:2],
        FileNameConvention(
            re.compile(r"(?P<temporality>reproc|forward)"),
            [
                FileNameFieldEnum(
                    "temporality",
                    Temporality,
                    case_type_encoded=CaseType.lower,
                    case_type_decoded=CaseType.upper,
                ),
            ],
            "{temporality!f}",
        ),
        _AVISO_L3_LR_SSH_LAYOUT_V2.conventions[2],
    ]
)

AVISO_L3_LR_SSH_LAYOUT = CompositeLayout(
    [_AVISO_L3_LR_SSH_LAYOUT_V3, _AVISO_L3_LR_SSH_LAYOUT_V2]
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
