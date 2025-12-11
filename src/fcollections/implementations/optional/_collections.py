from __future__ import annotations

from .._dac import _NetcdfFilesDatabaseDAC
from .._definitions import (
    XARRAY_TEMPORAL_NETCDFS,
    XARRAY_TEMPORAL_NETCDFS_NO_BACKEND,
)
from .._gridded_sla import _NetcdfFilesDatabaseGriddedSLA
from .._l2_lr_ssh import _NetcdfFilesDatabaseSwotLRL2
from .._l2_nadir import _NetcdfFilesDatabaseL2Nadir
from .._l3_lr_ssh import _NetcdfFilesDatabaseSwotLRL3
from .._l3_lr_ww import _NetcdfFilesDatabaseSwotLRWW
from .._l3_nadir import _NetcdfFilesDatabaseL3Nadir
from .._mur import _NetcdfFilesDatabaseMUR
from .._ocean_color import _NetcdfFilesDatabaseOC
from .._ohc import _NetcdfFilesDatabaseOHC
from .._sst import _NetcdfFilesDatabaseSST
from .._swh import _NetcdfFilesDatabaseSWH
from ._area_selectors import AreaSelector2D, TemporalSerieAreaSelector
from ._predicates import SwotGeometryPredicate
from ._reader import (
    GeoOpenMfDataset,
    GeoSwotReaderL2LRSSH,
    GeoSwotReaderL3LRSSH,
    GeoSwotReaderL3WW,
)


class GeoNetcdfFilesDatabaseSST(_NetcdfFilesDatabaseSST):
    reader = GeoOpenMfDataset(
        area_selector=AreaSelector2D(longitude="lon", latitude="lat"),
        xarray_options=XARRAY_TEMPORAL_NETCDFS,
    )


GeoNetcdfFilesDatabaseSST.__doc__ = _NetcdfFilesDatabaseSST.__doc__


class GeoNetcdfFilesDatabaseGriddedSLA(_NetcdfFilesDatabaseGriddedSLA):
    reader = GeoOpenMfDataset(
        area_selector=AreaSelector2D(), xarray_options=XARRAY_TEMPORAL_NETCDFS
    )


GeoNetcdfFilesDatabaseGriddedSLA.__doc__ = _NetcdfFilesDatabaseGriddedSLA.__doc__


class GeoNetcdfFilesDatabaseOHC(_NetcdfFilesDatabaseOHC):
    reader = GeoOpenMfDataset(
        area_selector=AreaSelector2D(),
        xarray_options=XARRAY_TEMPORAL_NETCDFS_NO_BACKEND,
    )


GeoNetcdfFilesDatabaseOHC.__doc__ = _NetcdfFilesDatabaseOHC.__doc__


class GeoNetcdfFilesDatabaseOC(_NetcdfFilesDatabaseOC):
    reader = GeoOpenMfDataset(
        area_selector=AreaSelector2D(longitude="lon", latitude="lat"),
        xarray_options=XARRAY_TEMPORAL_NETCDFS,
    )


GeoNetcdfFilesDatabaseOC.__doc__ = _NetcdfFilesDatabaseOC.__doc__


class GeoNetcdfFilesDatabaseSWH(_NetcdfFilesDatabaseSWH):
    reader = GeoOpenMfDataset(
        area_selector=TemporalSerieAreaSelector(),
        xarray_options=XARRAY_TEMPORAL_NETCDFS,
    )


GeoNetcdfFilesDatabaseSWH.__doc__ = _NetcdfFilesDatabaseSWH.__doc__


class GeoNetcdfFilesDatabaseMUR(_NetcdfFilesDatabaseMUR):
    reader = GeoOpenMfDataset(
        area_selector=AreaSelector2D(longitude="lon", latitude="lat"),
        xarray_options=XARRAY_TEMPORAL_NETCDFS,
    )


GeoNetcdfFilesDatabaseMUR.__doc__ = _NetcdfFilesDatabaseMUR.__doc__


class GeoNetcdfFilesDatabaseDAC(_NetcdfFilesDatabaseDAC):
    reader = GeoOpenMfDataset(
        area_selector=AreaSelector2D(),
        xarray_options=XARRAY_TEMPORAL_NETCDFS_NO_BACKEND,
    )


GeoNetcdfFilesDatabaseDAC.__doc__ = _NetcdfFilesDatabaseDAC.__doc__


class GeoNetcdfFilesDatabaseSwotLRL2(_NetcdfFilesDatabaseSwotLRL2):
    reader = GeoSwotReaderL2LRSSH()
    predicate_classes = [SwotGeometryPredicate]


GeoNetcdfFilesDatabaseSwotLRL2.__doc__ = _NetcdfFilesDatabaseSwotLRL2.__doc__


class GeoNetcdfFilesDatabaseSwotLRL3(_NetcdfFilesDatabaseSwotLRL3):
    reader = GeoSwotReaderL3LRSSH()
    predicate_classes = [SwotGeometryPredicate]


GeoNetcdfFilesDatabaseSwotLRL3.__doc__ = _NetcdfFilesDatabaseSwotLRL3.__doc__


class GeoNetcdfFilesDatabaseSwotLRWW(_NetcdfFilesDatabaseSwotLRWW):
    reader = GeoSwotReaderL3WW()
    predicate_classes = [SwotGeometryPredicate]


GeoNetcdfFilesDatabaseSwotLRWW.__doc__ = _NetcdfFilesDatabaseSwotLRWW.__doc__


class GeoNetcdfFilesDatabaseL3Nadir(_NetcdfFilesDatabaseL3Nadir):
    reader = GeoOpenMfDataset(
        area_selector=TemporalSerieAreaSelector(),
        xarray_options=XARRAY_TEMPORAL_NETCDFS,
    )


GeoNetcdfFilesDatabaseL3Nadir.__doc__ = _NetcdfFilesDatabaseL3Nadir.__doc__


class GeoNetcdfFilesDatabaseL2Nadir(_NetcdfFilesDatabaseL2Nadir):
    reader = GeoOpenMfDataset(
        area_selector=TemporalSerieAreaSelector(),
        xarray_options=XARRAY_TEMPORAL_NETCDFS,
    )


GeoNetcdfFilesDatabaseL2Nadir.__doc__ = _NetcdfFilesDatabaseL2Nadir.__doc__
