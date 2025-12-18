"""Sourced from
https://help.marine.copernicus.eu/en/articles/6820094-how-is-the-nomenclature-of-copernicus-marine-data-defined
"""

import re
from enum import Enum, auto

from fcollections.core import (
    CaseType,
    FileNameConvention,
    FileNameField,
    FileNameFieldEnum,
    FileNameFieldString,
)


class Origin(Enum):
    """Dataset origin."""

    CMEMS = auto()
    """Copernicus Marine."""
    C3S = auto()
    """C3S."""
    CCI = auto()
    """CCI."""
    OSISAF = auto()
    """OSISAF."""


class Group(Enum):
    """Dataset group."""

    OBS = auto()
    """Observations."""
    MOD = auto()
    """Model."""


class ProductClass(Enum):
    """Dataset product class."""

    SST = auto()
    """Sea Surface Temperature Thematic Assembly Center."""
    SL = auto()
    """Sea Level Thematic Assembly Center."""
    OC = auto()
    """Ocean Colour Thematic Assembly Center."""
    SI = auto()
    """Sea Ice."""
    WIND = auto()
    """Wind."""
    WAVE = auto()
    """Wave."""
    MOB = auto()
    """Multi observations."""
    INS = auto()
    """In-situ."""


class Area(Enum):
    """Dataset area of interest."""

    ATL = auto()
    """Atlantic."""
    ARC = auto()
    """Arctic."""
    ANT = auto()
    """Antarctic."""
    BAL = auto()
    """Baltic."""
    BLK = auto()
    """Black sea."""
    EUR = auto()
    """Europe."""
    GLO = auto()
    """Global."""
    IBI = auto()
    """Iberian sea."""
    MED = auto()
    """Mediterranean."""
    NWS = auto()
    """North west shelf."""


class Thematic(Enum):
    """Dataset thematic."""

    PHY = auto()
    """Physical."""
    BGC = auto()
    """Biogeochemical."""
    WAV = auto()
    """Wav."""
    PHYBGC = auto()
    """Phy BGC."""
    PHYBGCWAV = auto()
    """Wav Phy BGC."""


class Variable(Enum):
    """Dataset variable group."""

    TEMP = auto()
    """Temperature."""
    CUR = auto()
    """Currents."""
    CHL = auto()
    """Chlorophyll."""
    CAR = auto()
    """Carbon."""
    NUT = auto()
    """Nutrient."""
    GEOPHY = auto()
    """Geophy."""
    PLANKTON = auto()
    """Plancton."""
    TRANSP = auto()
    """Transparency."""
    OPTICS = auto()
    """Optics."""
    PP = auto()
    """Primary production."""
    MFLUX = auto()
    """Momentum flux."""
    WFLUX = auto()
    """Water flux."""
    HFLUX = auto()
    """Heat flux."""
    SWH = auto()
    """Surface Wave Height."""
    SSH = auto()
    """Sea surface Height."""
    REFLECTANCE = auto()
    """Reflectance."""


class ComplementaryInfo(Enum):
    """Product level enum."""

    L3 = auto()
    """Level 3."""
    L3S = auto()
    """Level 3 specific to SST_GLO_SST_L3S_NRT_OBSERVATIONS_010_010."""
    L4 = auto()
    """Level 4."""
    L4_DUACS = auto()
    """Level 4 specific to DUACS mappings."""


class DataType(Enum):
    """Dataset type."""

    MY = auto()
    """Multi-Years consistent time series."""
    MYINT = auto()
    """Interim data (about 1 month after the acquisition date)"""
    NRT = auto()
    """Near real time products."""
    ANFC = auto()
    """Analysis forecast."""
    HCST = auto()
    """Hindcast."""
    MYNRT = auto()
    """My NRT."""


class Typology(Enum):
    """Dataset typology."""

    I = auto()
    """Instantaneous."""
    M = auto()
    """Mean."""


class Sensors(Enum):
    # SEALEVEL_GLO_PHY_L3_MY_008_062
    # SEALEVEL_GLO_PHY_L3_NRT_008_044
    C2 = auto()
    C2N = auto()
    EN = auto()
    ENN = auto()
    E1 = auto()
    E1G = auto()
    E2 = auto()
    G2 = auto()
    H2A = auto()
    H2AG = auto()
    H2B = auto()
    J1 = auto()
    J1G = auto()
    J1N = auto()
    J2 = auto()
    J2G = auto()
    J3G = auto()
    AL = auto()
    ALG = auto()
    S3A = auto()
    S3B = auto()
    S6A = auto()
    S6A_LR = auto()
    SWON = auto()
    SWONC = auto()
    TP = auto()
    TPN = auto()
    # SEALEVEL_GLO_PHY_L4_NRT_008_046
    # SEALEVEL_GLO_PHY_L4_MY_008_047
    ALLSAT = auto()
    DEMO_ALLSAT_SWOTS = auto()
    ALLSAT_SWOS = auto()
    # WAVE_GLO_PHY_SWH_L3_NRT_014_001
    CFO = auto()
    H2C = auto()
    # SST_GLO_SST_L3S_NRT_OBSERVATIONS_010_010
    GIR = auto()
    PIR = auto()
    PMW = auto()
    # OCEANCOLOUR_GLO_BGC_L3_MY_009_103
    OLCI = auto()
    MULTI = auto()


_ENUM_FIELDS = [
    FileNameFieldEnum(
        "origin",
        Origin,
        case_type_decoded=CaseType.upper,
        case_type_encoded=CaseType.lower,
    ),
    FileNameFieldEnum(
        "group",
        Group,
        case_type_decoded=CaseType.upper,
        case_type_encoded=CaseType.lower,
    ),
    FileNameFieldEnum(
        "pc",
        ProductClass,
        case_type_decoded=CaseType.upper,
        case_type_encoded=CaseType.lower,
    ),
    FileNameFieldEnum(
        "area", Area, case_type_decoded=CaseType.upper, case_type_encoded=CaseType.lower
    ),
    FileNameFieldEnum(
        "thematic",
        Thematic,
        case_type_decoded=CaseType.upper,
        case_type_encoded=CaseType.lower,
    ),
    FileNameFieldEnum(
        "variable",
        Variable,
        case_type_decoded=CaseType.upper,
        case_type_encoded=CaseType.lower,
    ),
    FileNameFieldEnum(
        "type",
        DataType,
        case_type_decoded=CaseType.upper,
        case_type_encoded=CaseType.lower,
    ),
    FileNameFieldEnum(
        "typology",
        Typology,
        case_type_decoded=CaseType.upper,
        case_type_encoded=CaseType.lower,
    ),
]

temporal_resolution_field = FileNameFieldString("temporal_resolution")

MODEL = "(?P<origin>{0})_(?P<group>{1})(-(?P<pc>{2})){{0,1}}_(?P<area>{3})_(?P<thematic>{4})(-(?P<variable>{5})){{0,1}}(_(?P<type>{6})){{0,1}}_{8}_(?P<temporal_resolution>irr|P.*)(-(?P<typology>{7})){{0,1}}"


def build_convention(
    complementary: str = "(?P<complementary>.*)",
    complementary_fields: list[FileNameField] | None = None,
) -> FileNameConvention:

    if complementary_fields is None:
        complementary_fields = [FileNameFieldString("complementary")]

    regex_string = MODEL.format(
        *["|".join(field.choices()) for field in _ENUM_FIELDS], complementary
    )
    regex = re.compile(regex_string)

    return FileNameConvention(
        regex,
        [
            *_ENUM_FIELDS[:7],
            *complementary_fields,
            temporal_resolution_field,
            _ENUM_FIELDS[-1],
        ],
    )
