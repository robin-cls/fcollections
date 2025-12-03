"""This module provides convenient tools for loading netcdf files."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import fsspec
import fsspec.implementations.local as fs_loc
import numpy as np

from fcollections.core import (
    Deduplicator,
    DiscreteTimesMixin,
    FilesDatabase,
    OpenMfDataset,
    PeriodMixin,
    SubsetsUnmixer,
)

from ._conventions import (
    FileNameConventionDAC,
    FileNameConventionERA5,
    FileNameConventionGriddedSLA,
    FileNameConventionL2Nadir,
    FileNameConventionL3Nadir,
    FileNameConventionMUR,
    FileNameConventionOC,
    FileNameConventionOHC,
    FileNameConventionS1AOWI,
    FileNameConventionSST,
    FileNameConventionSWH,
    FileNameConventionSwotL2,
    FileNameConventionSwotL3,
    FileNameConventionSwotL3WW,
)
from ._readers import SwotReaderL2LRSSH, SwotReaderL3LRSSH, SwotReaderL3WW

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)
logging.captureWarnings(True)

# Options that works for most netcdf containing a time series
_XARRAY_TEMPORAL_NETCDFS: dict[str, str] = {
    'engine': 'h5netcdf',
    'combine': 'nested',
    'concat_dim': 'time'
}

# Options that works for netcdf containing a time series, but for which we need
# to relax the backend
_XARRAY_TEMPORAL_NETCDFS_NO_BACKEND: dict[str, str] = {
    'combine': 'nested',
    'concat_dim': 'time'
}


class _NetcdfFilesDatabaseSST(FilesDatabase, PeriodMixin):
    """Database mapping to select and read sea surface temperature Netcdf files
    in a local file system.

    Attributes
    ----------
    path: str
        path to directory containing NetCDF files
    """
    parser = FileNameConventionSST()
    reader = OpenMfDataset(_XARRAY_TEMPORAL_NETCDFS)
    sort_keys = 'time'


class _NetcdfFilesDatabaseGriddedSLA(FilesDatabase, PeriodMixin):
    """Database mapping to select and read gridded Sla Netcdf files in a local
    file system.

    Attributes
    ----------
    path: str
        path to directory containing NetCDF files
    """
    parser = FileNameConventionGriddedSLA()
    reader = OpenMfDataset(_XARRAY_TEMPORAL_NETCDFS)
    sort_keys = 'time'


class _NetcdfFilesDatabaseOHC(FilesDatabase, PeriodMixin):
    """Database mapping to select and read ocean heat content Netcdf files in a
    local file system.

    Attributes
    ----------
    path: str
        path to directory containing NetCDF files
    """
    parser = FileNameConventionOHC()
    reader = OpenMfDataset(_XARRAY_TEMPORAL_NETCDFS_NO_BACKEND)
    sort_keys = 'time'


class _NetcdfFilesDatabaseOC(FilesDatabase, PeriodMixin):
    """Database mapping to select and read ocean color Netcdf files in a local
    file system.

    Attributes
    ----------
    path: str
        path to directory containing NetCDF files
    """

    parser = FileNameConventionOC()
    reader = OpenMfDataset(_XARRAY_TEMPORAL_NETCDFS)
    sort_keys = 'time'


class _NetcdfFilesDatabaseSWH(FilesDatabase, PeriodMixin):
    """Database mapping to select and read significant wave height Netcdf files
    in a local file system.

    Attributes
    ----------
    path: str
        path to directory containing NetCDF files
    """
    parser = FileNameConventionSWH()
    reader = OpenMfDataset(_XARRAY_TEMPORAL_NETCDFS)
    sort_keys = 'time'


class NetcdfFilesDatabaseS1AOWI(FilesDatabase, PeriodMixin):
    """Database mapping to select and read S1A Ocean surface wind product
    Netcdf files in a local file system.

    Attributes
    ----------
    path: str
        path to directory containing NetCDF files
    """
    parser = FileNameConventionS1AOWI()
    reader = OpenMfDataset(xarray_options=_XARRAY_TEMPORAL_NETCDFS)
    sort_keys = 'time'


class NetcdfFilesDatabaseERA5(FilesDatabase, PeriodMixin):
    """Database mapping to select and read ERA5 reanalysis product Netcdf files
    in a local file system.

    Attributes
    ----------
    path: str
        path to directory containing NetCDF files
    """
    parser = FileNameConventionERA5()
    reader = OpenMfDataset(xarray_options=_XARRAY_TEMPORAL_NETCDFS)
    sort_keys = 'time'


class _NetcdfFilesDatabaseMUR(FilesDatabase, PeriodMixin):
    """Database mapping to select and read GHRSST Level 4 MUR Global Foundation
    Sea Surface Temperature Analysis product Netcdf file in a local file
    system.

    Attributes
    ----------
    path: str
        path to directory containing NetCDF files
    """
    parser = FileNameConventionMUR()
    reader = OpenMfDataset(_XARRAY_TEMPORAL_NETCDFS)
    sort_keys = 'time'


class _NetcdfFilesDatabaseDAC(FilesDatabase, DiscreteTimesMixin):
    """Database mapping to select and read Dynamic atmospheric correction
    Netcdf files in a local file system.

    Attributes
    ----------
    path: str
        path to directory containing NetCDF files
    """
    parser = FileNameConventionDAC()
    reader = OpenMfDataset(_XARRAY_TEMPORAL_NETCDFS_NO_BACKEND)
    metadata_injection = {'time': ('time', )}
    sort_keys = ['time']

    def __init__(self,
                 path: Path,
                 fs: fsspec.AbstractFileSystem = fs_loc.LocalFileSystem()):
        super().__init__(path, fs)
        super(FilesDatabase, self).__init__(np.timedelta64(6, 'h'))


class _NetcdfFilesDatabaseSwotLRL2(FilesDatabase, PeriodMixin):
    """Database mapping to select and read Swot LR L2 Netcdf files in a local
    file system.

    Attributes
    ----------
    path: str
        path to a directory containing NetCDF files
    """
    parser = FileNameConventionSwotL2()
    reader = SwotReaderL2LRSSH()
    sort_keys = 'time'

    # These keys determines an homogeneous subset
    unmixer = SubsetsUnmixer(partition_keys=['level', 'subset'])
    # We expect multiple versions in an homogeneous subset. Only one half orbit
    # record is tolerated so we deduplicate the multiple version with an
    # autopick
    deduplicator = Deduplicator(unique=('cycle_number', 'pass_number'),
                                auto_pick_last=('version', ))


class _NetcdfFilesDatabaseSwotLRL3(FilesDatabase, PeriodMixin):
    """Database mapping to select and read Swot LR L3 Netcdf files in a local
    file system.

    Attributes
    ----------
    path: str
        path to a directory containing NetCDF files
    """
    parser = FileNameConventionSwotL3()
    reader = SwotReaderL3LRSSH()
    sort_keys = 'time'

    # These keys determines an homogeneous subset. We expect no duplicates in
    # an homogeneous subset
    unmixer = SubsetsUnmixer(partition_keys=['version', 'subset'],
                             auto_pick_last=('version', ))


class _NetcdfFilesDatabaseSwotLRWW(FilesDatabase, PeriodMixin):
    """Database mapping to explore and read the L3_LR_WIND_WAVE product.

    Attributes
    ----------
    path
        path to a directory containing the NetCDF files
    fs
        File system hosting the files. Can be used to access local or remote
        (S3, FTP, ...) file systems. Underlying readers may not be compatible
        with all file systems implementations
    layout
        Layout of the subfolders. Useful to extract information and have an
        efficient file system scanning. The recommended layout can mismatch the
        current files organization, in which case the user can build its own or
        set this parameter to None

    See Also
    --------
    fcollections.implementations.AVISO_L3_LR_WINDWAVE_LAYOUT
        Recommended layout for the database
    """
    parser = FileNameConventionSwotL3WW()
    reader = SwotReaderL3WW()
    sort_keys = 'time'

    # These keys determines an homogeneous subset. We expect no duplicates in
    # an homogeneous subset
    unmixer = SubsetsUnmixer(partition_keys=['version', 'subset'],
                             auto_pick_last=('version', ))


class _NetcdfFilesDatabaseL3Nadir(FilesDatabase, PeriodMixin):
    """Database mapping to select and read L3 nadir Netcdf files in a local
    file system.

    Attributes
    ----------
    path: str
        path to a directory containing NetCDF files
    """
    parser = FileNameConventionL3Nadir()
    deduplicator = Deduplicator(unique=('time', ),
                                auto_pick_last=('production_date', ))
    unmixer = SubsetsUnmixer(partition_keys=['mission', 'resolution'])
    reader = OpenMfDataset(_XARRAY_TEMPORAL_NETCDFS)
    sort_keys = 'time'


class _NetcdfFilesDatabaseL2Nadir(FilesDatabase, PeriodMixin):
    """Database mapping to select and read L2 nadir Netcdf files in a local
    file system.

    Attributes
    ----------
    path: str
        path to a directory containing NetCDF files
    """
    parser = FileNameConventionL2Nadir()
    reader = OpenMfDataset(_XARRAY_TEMPORAL_NETCDFS)
    sort_keys = 'time'
