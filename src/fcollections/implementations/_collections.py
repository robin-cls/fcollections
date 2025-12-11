"""This module provides convenient tools for loading netcdf files."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)
logging.captureWarnings(True)

# Options that works for most netcdf containing a time series
_XARRAY_TEMPORAL_NETCDFS: dict[str, str] = {
    "engine": "h5netcdf",
    "combine": "nested",
    "concat_dim": "time",
}

# Options that works for netcdf containing a time series, but for which we need
# to relax the backend
_XARRAY_TEMPORAL_NETCDFS_NO_BACKEND: dict[str, str] = {
    "combine": "nested",
    "concat_dim": "time",
}
