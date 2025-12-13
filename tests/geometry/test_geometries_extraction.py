import numpy as np
import pytest
import xarray as xr

from fcollections.geometry import SwathGeometriesBuilder


def build_fake_swath(pass_number=2, lon0=None, num_lines=9860, num_pixels=69):
    np.random.seed(pass_number)

    if lon0 is None:
        lon0 = 67 + pass_number * 166

    indices = np.linspace(-1, 1, num_lines).reshape(-1, 1)
    ds = xr.Dataset()

    # création latitude
    sign = -((-1) ** pass_number)

    dx = -0.3 - 0.8 * ((1.1 * indices) ** 2)
    array = sign * np.sin(indices * 1.25) * 80
    dx = dx * np.linspace(-100, 100, num_pixels).reshape(1, num_pixels) / 100

    ds["latitude"] = (["num_lines", "num_pixels"], array + dx)

    # création longitude
    array = lon0 + 0.24 * (indices * 5) ** 3.0 + indices * 6 + 51 * indices**11
    dx = 0.02 + 0.031 * (0.8 * indices**2 + 0.08 * indices**30)
    dx = -dx * np.linspace(-34, 34, num_pixels).reshape(1, num_pixels) * 1

    ds["longitude"] = (["num_lines", "num_pixels"], (array + dx) % 360)

    # création data
    shape = ds.longitude.shape
    start = np.zeros(shape, dtype=np.float32)

    start[:3, :] = np.nan
    start[-3:, :] = np.nan

    dx = (np.random.normal(size=shape[0])) * (1 / num_lines)
    dx = np.cumsum(dx)
    dx = np.convolve(dx, np.ones(11), mode="same")

    dx = np.tile(dx, (shape[1], 1)).T

    start = start + dx

    dy = (np.random.normal(size=shape[1])) * (1 / num_lines) * 2

    dy = np.cumsum(dy)
    dy = np.convolve(dy, np.ones(3), mode="same")
    dy = np.tile(dy, (shape[0], 1))

    start = start + dy

    ds["sla"] = (["num_lines", "num_pixels"], start)
    ds["pass_number"] = (
        ["num_lines"],
        np.zeros(shape[0], dtype=np.uint8) + pass_number,
    )
    ds["cycle_number"] = (["num_lines"], 1 + np.zeros(shape[0], dtype=np.uint8))

    time = pass_number * 3066 + np.linspace(0, 3065, shape[0])
    time = np.datetime64("2023-11-01T00:00:00") + (time * 1000).astype(int).astype(
        "timedelta64[ms]"
    )
    ds["time"] = (["num_lines"], time.astype("datetime64[ns]"))
    ds = ds.set_coords(["longitude", "latitude"])
    return ds


@pytest.fixture()
def builder():
    return SwathGeometriesBuilder()


@pytest.fixture()
def ds_karin():
    return build_fake_swath()


def test_build(builder, ds_karin):
    geom = builder.build(ds=ds_karin)
    assert geom.pass_number[0] == 0
    assert geometry_length(geom.geometry[0]) == 500

    geom = builder.build(ds=ds_karin, pass_number=512, nb_points=35)

    assert geom.pass_number[0] == 512
    assert geometry_length(geom.geometry[0]) == 35


def test_build_mutiple_swath(builder, ds_karin):
    dataset = xr.concat([ds_karin, ds_karin], dim="num_lines")
    with pytest.raises(KeyError):
        builder.build(ds=dataset)


def geometry_flatten(geom):
    if hasattr(geom, "geoms"):  # Multi<Type> / GeometryCollection
        for g in geom.geoms:
            yield from geometry_flatten(g)
    elif hasattr(geom, "interiors"):  # Polygon
        yield geom.exterior
        yield from geom.interiors
    else:  # Point / LineString
        yield geom


def geometry_length(geom):
    return sum(len(g.coords) for g in geometry_flatten(geom))
