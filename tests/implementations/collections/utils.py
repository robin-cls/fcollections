import numpy as np
import xarray as xr

from fcollections.geometry import query_geometries

num_lines, num_pixels = 9860, 69
num_nadir = int(np.ceil(num_lines / 3))


def brute_force_geographical_selection(
    ds: xr.Dataset, lon_min: float, lat_min: float, lon_max: float, lat_max: float
) -> xr.Dataset:
    mask = (
        (ds["longitude"] >= lon_min)
        & (ds["longitude"] <= lon_max)
        & (ds["latitude"] >= lat_min)
        & (ds["latitude"] <= lat_max)
    )

    # Only crop variables along the mask dimension. Else xarray will broadcast
    # the other variables along said dimensions
    to_crop = {v for v in ds.variables if set(mask.dims) & set(ds[v].dims) != set()}
    ds_crop = ds[to_crop].where(mask, drop=True)
    remains = ds[set(ds.variables) - to_crop]
    ds_crop.update(remains)
    return ds_crop


def extract_box_from_polygon(
    pass_number: int,
    box_size: float = 5.0,
    latitude: float = 0.0,
    phase: str = "calval",
) -> tuple[float, float, float, float]:
    polygon = query_geometries(pass_number, phase).geometry.values[0]
    xx, yy = polygon.exterior.coords.xy
    xx, yy = np.array(xx.tolist()), np.array(yy.tolist())

    index = np.argmin(abs(yy - latitude))
    lon_center, lat_center = xx[index], yy[index]
    bbox = (
        lon_center - box_size,
        lat_center - box_size,
        lon_center + box_size,
        lat_center + box_size,
    )
    return bbox
