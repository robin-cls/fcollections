from __future__ import annotations

from .._collections import (
    _XARRAY_TEMPORAL_NETCDFS,
    _XARRAY_TEMPORAL_NETCDFS_NO_BACKEND,
    _NetcdfFilesDatabaseDAC,
    _NetcdfFilesDatabaseGriddedSLA,
    _NetcdfFilesDatabaseL2Nadir,
    _NetcdfFilesDatabaseL3Nadir,
    _NetcdfFilesDatabaseMUR,
    _NetcdfFilesDatabaseOC,
    _NetcdfFilesDatabaseOHC,
    _NetcdfFilesDatabaseSWH,
    _NetcdfFilesDatabaseSwotLRL2,
    _NetcdfFilesDatabaseSwotLRL3,
    _NetcdfFilesDatabaseSwotLRWW,
)
from .._sst import _NetcdfFilesDatabaseSST
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
        xarray_options=_XARRAY_TEMPORAL_NETCDFS,
    )


GeoNetcdfFilesDatabaseSST.__doc__ = _NetcdfFilesDatabaseSST.__doc__


class GeoNetcdfFilesDatabaseGriddedSLA(_NetcdfFilesDatabaseGriddedSLA):
    reader = GeoOpenMfDataset(
        area_selector=AreaSelector2D(), xarray_options=_XARRAY_TEMPORAL_NETCDFS
    )


GeoNetcdfFilesDatabaseGriddedSLA.__doc__ = _NetcdfFilesDatabaseGriddedSLA.__doc__


class GeoNetcdfFilesDatabaseOHC(_NetcdfFilesDatabaseOHC):
    reader = GeoOpenMfDataset(
        area_selector=AreaSelector2D(),
        xarray_options=_XARRAY_TEMPORAL_NETCDFS_NO_BACKEND,
    )


GeoNetcdfFilesDatabaseOHC.__doc__ = _NetcdfFilesDatabaseOHC.__doc__


class GeoNetcdfFilesDatabaseOC(_NetcdfFilesDatabaseOC):
    reader = GeoOpenMfDataset(
        area_selector=AreaSelector2D(longitude="lon", latitude="lat"),
        xarray_options=_XARRAY_TEMPORAL_NETCDFS,
    )


GeoNetcdfFilesDatabaseOC.__doc__ = _NetcdfFilesDatabaseOC.__doc__


class GeoNetcdfFilesDatabaseSWH(_NetcdfFilesDatabaseSWH):
    reader = GeoOpenMfDataset(
        area_selector=TemporalSerieAreaSelector(),
        xarray_options=_XARRAY_TEMPORAL_NETCDFS,
    )


GeoNetcdfFilesDatabaseSWH.__doc__ = _NetcdfFilesDatabaseSWH.__doc__


class GeoNetcdfFilesDatabaseMUR(_NetcdfFilesDatabaseMUR):
    reader = GeoOpenMfDataset(
        area_selector=AreaSelector2D(longitude="lon", latitude="lat"),
        xarray_options=_XARRAY_TEMPORAL_NETCDFS,
    )


GeoNetcdfFilesDatabaseMUR.__doc__ = _NetcdfFilesDatabaseMUR.__doc__


class GeoNetcdfFilesDatabaseDAC(_NetcdfFilesDatabaseDAC):
    reader = GeoOpenMfDataset(
        area_selector=AreaSelector2D(),
        xarray_options=_XARRAY_TEMPORAL_NETCDFS_NO_BACKEND,
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
        xarray_options=_XARRAY_TEMPORAL_NETCDFS,
    )


GeoNetcdfFilesDatabaseL3Nadir.__doc__ = _NetcdfFilesDatabaseL3Nadir.__doc__


class GeoNetcdfFilesDatabaseL2Nadir(_NetcdfFilesDatabaseL2Nadir):
    reader = GeoOpenMfDataset(
        area_selector=TemporalSerieAreaSelector(),
        xarray_options=_XARRAY_TEMPORAL_NETCDFS,
    )


GeoNetcdfFilesDatabaseL2Nadir.__doc__ = _NetcdfFilesDatabaseL2Nadir.__doc__
