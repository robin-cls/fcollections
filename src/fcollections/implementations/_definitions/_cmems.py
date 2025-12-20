"""Definition of the dataset id convention. Described in the following link
https://help.marine.copernicus.eu/en/articles/6820094-how-is-the-nomenclature-of-copernicus-marine-data-defined

Each product will define its own regex and fields for a free complementary info
section. The module provides two utilities to build the final convention of a
product with the complementary information.
"""

import re
from enum import Enum, auto

from fcollections.core import (
    CaseType,
    FileNameConvention,
    FileNameField,
    FileNameFieldEnum,
    FileNameFieldInteger,
    FileNameFieldISODuration,
    FileNameFieldString,
    Layout,
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
    """Aggregation of sensors for multiple CMEMS products.

    - SEALEVEL_GLO_PHY_L3_MY_008_062
    - SEALEVEL_GLO_PHY_L3_NRT_008_044
    - SEALEVEL_GLO_PHY_L4_NRT_008_046
    - SEALEVEL_GLO_PHY_L4_MY_008_047
    - WAVE_GLO_PHY_SWH_L3_NRT_014_001
    - SST_GLO_SST_L3S_NRT_OBSERVATIONS_010_010
    - OCEANCOLOUR_GLO_BGC_L3_MY_009_103
    """

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
    J3 = auto()
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
    SWOT = auto()
    # SST_GLO_SST_L3S_NRT_OBSERVATIONS_010_010
    GIR = auto()
    PIR = auto()
    PMW = auto()
    # OCEANCOLOUR_GLO_BGC_L3_MY_009_103
    OLCI = auto()
    MULTI = auto()


class FileNameFieldEnumOptional(FileNameFieldEnum):
    """Specific field created for the CMEMS dataset id convention.

    In the convention regex, some groups can be optional (-ssh). These
    groups are heasier to handle if the field can handle the hyphen
    (?P<variables>-ssh)

    In order to have the value, decoding/encoding must remove/add the
    hyphen.
    """

    def decode(self, input_string: str) -> type[Enum]:
        if input_string.startswith("-"):
            return super().decode(input_string[1:])

    def encode(self, data: type[Enum] | None) -> str:
        return "" if data is None else f"-{super().encode(data)}"


class FileNameFieldStringOptional(FileNameFieldString):
    """Specific field created for the CMEMS dataset id convention.

    In the convention regex, some groups can be optional (_202422).
    These groups are heasier to handle if the field can handle the
    underscore (?P<version>_\\d{6})

    To work with a useful value, decoding/encoding must remove/add the
    underscore.
    """

    def decode(self, input_string: str) -> str:
        if input_string.startswith("_"):
            return super().decode(input_string[1:])

    def encode(self, data: str | None) -> str:
        return "" if data is None else f"_{super().encode(data)}"


CMEMS_DATASET_ID_FIELDS = [
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
    FileNameFieldEnumOptional(
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
    FileNameFieldEnumOptional(
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
    FileNameFieldEnumOptional(
        "typology",
        Typology,
        case_type_decoded=CaseType.upper,
        case_type_encoded=CaseType.lower,
    ),
    FileNameFieldEnum(
        "sensor",
        Sensors,
        case_type_decoded=CaseType.upper,
        case_type_encoded=CaseType.lower,
        underscore_encoded=False,
    ),
]

_MODEL_FRAGMENTS = [
    "(?P<origin>{0})",
    "_(?P<group>{1})(?P<pc>{2}){{0,1}}",
    "_(?P<area>{3})",
    "_(?P<thematic>{4})(?P<variable>{5}){{0,1}}",
    "(_(?P<type>{6})){{0,1}}",
    "_{8}",
    "_(?P<temporal_resolution>irr|(P.*(Y|M|W|D|H|M|S)))(?P<typology>{7}){{0,1}}",
    "(?P<version>_\\d{{6}}){{0,1}}",
]

_MODEL = "".join(_MODEL_FRAGMENTS)


def build_convention(
    complementary: str,
    complementary_fields: list[FileNameField],
    complementary_generation_string: str,
    strict: bool = False,
) -> FileNameConvention:
    """Build CMEMS dataset id convention.

    Dataset ID convention reserves a free section that each product can use to
    put specific information. These specificities must be given in the form of
    a regex fragment, fields and generation_string matching the regex.

    In case the file name convention is based on the dataset_id convention,
    there can be a confusion of layouts during parsing: a file node could be
    parsed by the folder/datasetid convention, leading to an incomplete record.

    To avoid this case, the ``strict`` argument can be set to enforce that the
    datasetid name convention regex will match the whole input

    Parameters
    ----------
    complementary
        The regex for complementary information section
    complementary_fields
        The fields for complementary information section
    complementary_generation_string
        The generation string for complementary information section
    strict
        True to enforce ``^...$`` for the returned file name convention regex

    Returns
    -------
    :
        A file name convention matching the product
    """

    regex_string = _MODEL.format(
        *["|".join(field.choices()) for field in CMEMS_DATASET_ID_FIELDS[:-1]],
        complementary,
    )
    if strict:
        # Enforce full match, useful if filename convention is based on dataset
        # id convention
        regex_string = "^" + regex_string + "$"

    regex = re.compile(regex_string)

    generation_fragments = [
        "{origin!f}",
        "_{group!f}{pc!f}",
        "_{area!f}",
        "_{thematic!f}{variable!f}",
        "_{type!f}",
        "_" + complementary_generation_string,
        "_{temporal_resolution!f}{typology!f}",
        "{version!f}",  # Optional fragment
    ]

    return FileNameConvention(
        regex,
        [
            *CMEMS_DATASET_ID_FIELDS[:7],
            *complementary_fields,
            FileNameFieldISODuration("temporal_resolution"),
            CMEMS_DATASET_ID_FIELDS[-2],
            FileNameFieldStringOptional("version"),
        ],
        "".join(generation_fragments),
    )


def build_layout(
    dataset_id_convention: FileNameConvention, filename_convention: FileNameConvention
) -> Layout:
    """Add year and month levels to build a full CMEMS layout.

    CMEMS layout are usually organized as <dataset_id>/<year>/<month>/<file>.
    Given the dataset_id and filename conventions, this utility adds the two
    intermediary levels

    Parameters
    ----------
    dataset_id_convention
        Dataset ID convention
    filename_convention
        File name convention

    Returns
    -------
    :
        The full product layout
    """
    return Layout(
        [
            dataset_id_convention,
            FileNameConvention(
                re.compile(r"^(?P<year>\d{4})$"),
                [FileNameFieldInteger("year")],
                "{year}",
            ),
            FileNameConvention(
                re.compile(r"^(?P<month>\d{2})$"),
                [FileNameFieldInteger("month")],
                "{month:0>2d}",
            ),
            filename_convention,
        ]
    )
