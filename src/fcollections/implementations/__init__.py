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

    from ._ocean_color import _NetcdfFilesDatabaseOC as NetcdfFilesDatabaseOC
    from ._dac import _NetcdfFilesDatabaseDAC as NetcdfFilesDatabaseDAC
    from ._gridded_sla import (
        _NetcdfFilesDatabaseGriddedSLA as NetcdfFilesDatabaseGriddedSLA,
    )
    from ._l2_nadir import _NetcdfFilesDatabaseL2Nadir as NetcdfFilesDatabaseL2Nadir
    from ._l3_nadir import _NetcdfFilesDatabaseL3Nadir as NetcdfFilesDatabaseL3Nadir
    from ._mur import _NetcdfFilesDatabaseMUR as NetcdfFilesDatabaseMUR
    from ._ohc import _NetcdfFilesDatabaseOHC as NetcdfFilesDatabaseOHC
    from ._swh import _NetcdfFilesDatabaseSWH as NetcdfFilesDatabaseSWH
    from ._l2_lr_ssh import _NetcdfFilesDatabaseSwotLRL2 as NetcdfFilesDatabaseSwotLRL2
    from ._l3_lr_ssh import _NetcdfFilesDatabaseSwotLRL3 as NetcdfFilesDatabaseSwotLRL3
    from ._l3_lr_ww import _NetcdfFilesDatabaseSwotLRWW as NetcdfFilesDatabaseSwotLRWW
    from ._swh import _NetcdfFilesDatabaseSWH as NetcdfFilesDatabaseSWH
    from ._sst import _NetcdfFilesDatabaseSST as NetcdfFilesDatabaseSST

from ._dac import FileNameConventionDAC
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
from ._era5 import FileNameConventionERA5, NetcdfFilesDatabaseERA5
from ._gridded_sla import AVISO_L4_SWOT_LAYOUT as _AVISO_L4_SWOT_LAYOUT
from ._gridded_sla import CMEMS_NADIR_SSHA_LAYOUT as _CMEMS_NADIR_SSHA_LAYOUT
from ._gridded_sla import (
    FileNameConventionGriddedSLA,
    FileNameConventionGriddedSLAInternal,
)
from ._l2_lr_ssh import AVISO_L2_LR_SSH_LAYOUT as _AVISO_L2_LR_SSH_LAYOUT
from ._l2_lr_ssh import FileNameConventionSwotL2
from ._l2_nadir import FileNameConventionL2Nadir
from ._l3_lr_ssh import AVISO_L3_LR_SSH_LAYOUT as _AVISO_L3_LR_SSH_LAYOUT
from ._l3_lr_ssh import FileNameConventionSwotL3
from ._l3_lr_ww import FileNameConventionSwotL3WW
from ._l3_nadir import FileNameConventionL3Nadir
from ._mur import FileNameConventionMUR
from ._ocean_color import FileNameConventionOC
from ._ohc import FileNameConventionOHC
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
from ._s1aowi import FileNameConventionS1AOWI, NetcdfFilesDatabaseS1AOWI
from ._sst import FileNameConventionSST
from ._swh import FileNameConventionSWH

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
