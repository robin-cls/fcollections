import warnings

from fcollections.core import Layout

__all__ = []

try:
    from .optional import GeoNetcdfFilesDatabaseDAC as NetcdfFilesDatabaseDAC
    from .optional import (
        GeoNetcdfFilesDatabaseGriddedSLA as NetcdfFilesDatabaseGriddedSLA,
    )
    from .optional import GeoNetcdfFilesDatabaseL2Nadir as NetcdfFilesDatabaseL2Nadir
    from .optional import GeoNetcdfFilesDatabaseL3Nadir as NetcdfFilesDatabaseL3Nadir
    from .optional import GeoNetcdfFilesDatabaseMUR as NetcdfFilesDatabaseMUR
    from .optional import GeoNetcdfFilesDatabaseOC as NetcdfFilesDatabaseOC
    from .optional import GeoNetcdfFilesDatabaseOHC as NetcdfFilesDatabaseOHC
    from .optional import GeoNetcdfFilesDatabaseSST as NetcdfFilesDatabaseSST
    from .optional import GeoNetcdfFilesDatabaseSWH as NetcdfFilesDatabaseSWH
    from .optional import GeoNetcdfFilesDatabaseSwotLRL2 as NetcdfFilesDatabaseSwotLRL2
    from .optional import GeoNetcdfFilesDatabaseSwotLRL3 as NetcdfFilesDatabaseSwotLRL3
    from .optional import GeoNetcdfFilesDatabaseSwotLRWW as NetcdfFilesDatabaseSwotLRWW

except ImportError:
    msg = (
        "Could not import area selection package, the optional dependencies"
        "shapely, pyinterp and geopandas are not installed. Geographical "
        "filters in queries and area selection cropping in datasets will be "
        "disabled"
    )
    warnings.warn(msg, ImportWarning)

    from ._collections import (
        _NetcdfFilesDatabaseOC as NetcdfFilesDatabaseOC,
        _NetcdfFilesDatabaseDAC as NetcdfFilesDatabaseDAC,
        _NetcdfFilesDatabaseGriddedSLA as NetcdfFilesDatabaseGriddedSLA,
        _NetcdfFilesDatabaseL2Nadir as NetcdfFilesDatabaseL2Nadir,
        _NetcdfFilesDatabaseL3Nadir as NetcdfFilesDatabaseL3Nadir,
        _NetcdfFilesDatabaseMUR as NetcdfFilesDatabaseMUR,
        _NetcdfFilesDatabaseOHC as NetcdfFilesDatabaseOHC,
        _NetcdfFilesDatabaseSWH as NetcdfFilesDatabaseSWH,
        _NetcdfFilesDatabaseSwotLRL2 as NetcdfFilesDatabaseSwotLRL2,
        _NetcdfFilesDatabaseSwotLRL3 as NetcdfFilesDatabaseSwotLRL3,
        _NetcdfFilesDatabaseSwotLRWW as NetcdfFilesDatabaseSwotLRWW,
        _NetcdfFilesDatabaseSWH as NetcdfFilesDatabaseSWH,
        _NetcdfFilesDatabaseSwotLRL2 as NetcdfFilesDatabaseSwotLRL2,
        _NetcdfFilesDatabaseSwotLRL3 as NetcdfFilesDatabaseSwotLRL3,
        _NetcdfFilesDatabaseSwotLRWW as NetcdfFilesDatabaseSwotLRWW,
    )
    from ._sst import _NetcdfFilesDatabaseSST as NetcdfFilesDatabaseSST

from ._collections import NetcdfFilesDatabaseERA5, NetcdfFilesDatabaseS1AOWI
from ._conventions import AVISO_L2_LR_SSH_LAYOUT as _AVISO_L2_LR_SSH_LAYOUT
from ._conventions import AVISO_L3_LR_SSH_LAYOUT as _AVISO_L3_LR_SSH_LAYOUT
from ._conventions import AVISO_L4_SWOT_LAYOUT as _AVISO_L4_SWOT_LAYOUT
from ._conventions import CMEMS_NADIR_SSHA_LAYOUT as _CMEMS_NADIR_SSHA_LAYOUT
from ._conventions import (
    FileNameConventionDAC,
    FileNameConventionERA5,
    FileNameConventionGriddedSLA,
    FileNameConventionGriddedSLAInternal,
    FileNameConventionL2Nadir,
    FileNameConventionL3Nadir,
    FileNameConventionMUR,
    FileNameConventionOC,
    FileNameConventionOHC,
    FileNameConventionS1AOWI,
    FileNameConventionSWH,
    FileNameConventionSwotL2,
    FileNameConventionSwotL3,
    FileNameConventionSwotL3WW,
)
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
from ._products import (
    L2Version,
    L2VersionField,
    ProductSubset,
    Timeliness,
    build_version_parser,
)
from ._readers import (
    StackLevel,
    SwotReaderL2LRSSH,
    SwotReaderL3LRSSH,
    SwotReaderL3WW,
)
from ._sst import FileNameConventionSST

# Realiased constant to be picked up by Sphinx to work around autodoc limitation
#: Layout on Aviso FTP, Aviso TDS for the L2_LR_SSH product
AVISO_L2_LR_SSH_LAYOUT: Layout = _AVISO_L2_LR_SSH_LAYOUT
#: Layout on Aviso FTP, Aviso TDS for the L3_LR_SSH product
AVISO_L3_LR_SSH_LAYOUT: Layout = _AVISO_L3_LR_SSH_LAYOUT
#: Layout on Aviso FTP, Aviso TDS for the L3_LR_WindWave product
AVISO_L3_LR_WINDWAVE_LAYOUT: Layout = _AVISO_L3_LR_SSH_LAYOUT
#: Layout on Aviso FTP, Aviso TDS for the L4 Sea Level Anomaly experimental product including karin measurements
AVISO_L4_SWOT_LAYOUT: Layout = _AVISO_L4_SWOT_LAYOUT
#: Layout on CMEMS for the Level 3 SSHA nadir products
CMEMS_NADIR_SSHA_LAYOUT: Layout = _CMEMS_NADIR_SSHA_LAYOUT

__all__ = [
    "NetcdfFilesDatabaseSwotLRL2",
    "NetcdfFilesDatabaseSwotLRL3",
    "NetcdfFilesDatabaseGriddedSLA",
    "NetcdfFilesDatabaseSST",
    "NetcdfFilesDatabaseDAC",
    "NetcdfFilesDatabaseOC",
    "NetcdfFilesDatabaseSWH",
    "NetcdfFilesDatabaseOHC",
    "NetcdfFilesDatabaseS1AOWI",
    "NetcdfFilesDatabaseMUR",
    "NetcdfFilesDatabaseERA5",
    "NetcdfFilesDatabaseL2Nadir",
    "NetcdfFilesDatabaseL3Nadir",
    "NetcdfFilesDatabaseSwotLRWW",
    "FileNameConventionERA5",
    "ProductSubset",
    "ProductGroup",
    "FileNameConventionOC",
    "FileNameConventionGriddedSLA",
    "FileNameConventionGriddedSLAInternal",
    "FileNameConventionSST",
    "FileNameConventionDAC",
    "FileNameConventionSwotL2",
    "FileNameConventionSwotL3",
    "FileNameConventionSwotL3WW",
    "FileNameConventionOHC",
    "FileNameConventionS1AOWI",
    "FileNameConventionMUR",
    "FileNameConventionSWH",
    "FileNameConventionL2Nadir",
    "FileNameConventionL3Nadir",
    "Timeliness",
    "L2Version",
    "L2VersionField",
    "ProductType",
    "build_version_parser",
    "Sensor",
    "OCVariable",
    "ProductLevel",
    "AcquisitionMode",
    "S1AOWIProductType",
    "Delay",
    "S1AOWISlicePostProcessing",
    "AVISO_L2_LR_SSH_LAYOUT",
    "AVISO_L3_LR_SSH_LAYOUT",
    "AVISO_L3_LR_WINDWAVE_LAYOUT",
    "AVISO_L4_SWOT_LAYOUT",
    "CMEMS_NADIR_SSHA_LAYOUT",
    "SwotReaderL2LRSSH",
    "SwotReaderL3LRSSH",
    "SwotReaderL3WW",
    "StackLevel",
    "Temporality",
]
