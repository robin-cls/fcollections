from fcollections.core import Layout

__all__ = []

from ._dac import (
    BasicNetcdfFilesDatabaseDAC,
    FileNameConventionDAC,
    NetcdfFilesDatabaseDAC,
)
from ._definitions import (
    AcquisitionMode,
    Delay,
    OCVariable,
    ProductLevel,
    ProductSubset,
    S1AOWIProductType,
    S1AOWISlicePostProcessing,
    Sensor,
    Temporality,
)
from ._era5 import FileNameConventionERA5, NetcdfFilesDatabaseERA5
from ._gridded_sla import AVISO_L4_SWOT_LAYOUT as _AVISO_L4_SWOT_LAYOUT
from ._gridded_sla import CMEMS_NADIR_SSHA_LAYOUT as _CMEMS_NADIR_SSHA_LAYOUT
from ._gridded_sla import (
    BasicNetcdfFilesDatabaseGriddedSLA,
    FileNameConventionGriddedSLA,
    FileNameConventionGriddedSLAInternal,
    NetcdfFilesDatabaseGriddedSLA,
)
from ._l2_lr_ssh import AVISO_L2_LR_SSH_LAYOUT as _AVISO_L2_LR_SSH_LAYOUT
from ._l2_lr_ssh import (
    BasicNetcdfFilesDatabaseSwotLRL2,
    FileNameConventionSwotL2,
    L2Version,
    L2VersionField,
    NetcdfFilesDatabaseSwotLRL2,
    Timeliness,
    build_version_parser,
)
from ._l2_nadir import (
    BasicNetcdfFilesDatabaseL2Nadir,
    FileNameConventionL2Nadir,
    NetcdfFilesDatabaseL2Nadir,
)
from ._l3_lr_ssh import AVISO_L3_LR_SSH_LAYOUT as _AVISO_L3_LR_SSH_LAYOUT
from ._l3_lr_ssh import (
    BasicNetcdfFilesDatabaseSwotLRL3,
    FileNameConventionSwotL3,
    NetcdfFilesDatabaseSwotLRL3,
)
from ._l3_lr_ww import (
    BasicNetcdfFilesDatabaseSwotLRWW,
    FileNameConventionSwotL3WW,
    NetcdfFilesDatabaseSwotLRWW,
)
from ._l3_nadir import (
    BasicNetcdfFilesDatabaseL3Nadir,
    FileNameConventionL3Nadir,
    NetcdfFilesDatabaseL3Nadir,
)
from ._mur import (
    BasicNetcdfFilesDatabaseMUR,
    FileNameConventionMUR,
    NetcdfFilesDatabaseMUR,
)
from ._ocean_color import (
    BasicNetcdfFilesDatabaseOC,
    FileNameConventionOC,
    NetcdfFilesDatabaseOC,
)
from ._ohc import (
    BasicNetcdfFilesDatabaseOHC,
    FileNameConventionOHC,
    NetcdfFilesDatabaseOHC,
)
from ._readers import (
    StackLevel,
    SwotReaderL2LRSSH,
    SwotReaderL3LRSSH,
    SwotReaderL3WW,
)
from ._s1aowi import FileNameConventionS1AOWI, NetcdfFilesDatabaseS1AOWI
from ._sst import (
    BasicNetcdfFilesDatabaseSST,
    FileNameConventionSST,
    NetcdfFilesDatabaseSST,
)
from ._swh import (
    BasicNetcdfFilesDatabaseSWH,
    FileNameConventionSWH,
    NetcdfFilesDatabaseSWH,
)

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
    "BasicNetcdfFilesDatabaseDAC",
    "BasicNetcdfFilesDatabaseGriddedSLA",
    "BasicNetcdfFilesDatabaseSwotLRL2",
    "BasicNetcdfFilesDatabaseL2Nadir",
    "BasicNetcdfFilesDatabaseSwotLRL3",
    "BasicNetcdfFilesDatabaseSwotLRWW",
    "BasicNetcdfFilesDatabaseL3Nadir",
    "BasicNetcdfFilesDatabaseMUR",
    "BasicNetcdfFilesDatabaseOC",
    "BasicNetcdfFilesDatabaseOHC",
    "BasicNetcdfFilesDatabaseSST",
    "NetcdfFilesDatabaseSwotLRL2",
    "NetcdfFilesDatabaseSwotLRL3",
    "NetcdfFilesDatabaseGriddedSLA",
    "NetcdfFilesDatabaseSST",
    "NetcdfFilesDatabaseDAC",
    "NetcdfFilesDatabaseOC",
    "NetcdfFilesDatabaseSWH",
    "BasicNetcdfFilesDatabaseSWH",
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
