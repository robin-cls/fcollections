from enum import Enum, auto

# This generic message can be used as a warning if the optional module import
# fails. In which case the implementations should define a FilesDatabase with
# less functionalities
MISSING_OPTIONAL_DEPENDENCIES_MESSAGE = (
    "Could not import area selection package, the optional dependencies"
    "shapely, pyinterp and geopandas are not installed. Geographical "
    "filters in queries and area selection cropping in datasets will be "
    "disabled"
)

# Options that works for most netcdf containing a time series
XARRAY_TEMPORAL_NETCDFS: dict[str, str] = {
    "engine": "h5netcdf",
    "combine": "nested",
    "concat_dim": "time",
}

# Options that works for netcdf containing a time series, but for which we need
# to relax the backend
XARRAY_TEMPORAL_NETCDFS_NO_BACKEND: dict[str, str] = {
    "combine": "nested",
    "concat_dim": "time",
}


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


class ProductLevel(Enum):
    """Product level enum."""

    L1A = auto()
    L1B = auto()
    L2 = auto()
    L3 = auto()
    L4 = auto()


class Delay(Enum):
    NRT = auto()
    DT = auto()
    MY = auto()
    MYINT = auto()
