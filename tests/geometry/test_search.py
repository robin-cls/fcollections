import numpy as np
import pytest

from fcollections.geometry import query_geometries, query_half_orbits_intersect


@pytest.mark.parametrize(
    "phase, pass_numbers",
    [
        ("bad", [1]),
        ("calval", [29]),
        ("science", [585]),
    ],
)
def test_query_polygons_error(phase, pass_numbers):
    with pytest.raises(KeyError):
        query_geometries(pass_numbers, phase)


@pytest.mark.parametrize(
    "phase, pass_numbers", [("calval", [25, 26]), ("science", [532, 579])]
)
def test_query_geometries(phase, pass_numbers):
    swath_geom = query_geometries(pass_numbers, phase)
    assert list(swath_geom.sort_values("pass_number").pass_number) == list(pass_numbers)
    assert len(swath_geom.geometry) == len(pass_numbers)


def test_query_geometries_int():
    df_list = query_geometries([25], "calval")
    df_int = query_geometries(25, "calval")
    assert df_list.equals(df_int)


@pytest.mark.parametrize(
    "phase, bbox, result_passes",
    [
        ("science", (-180, -90, 179.99, 90), np.array([532, 579])),
        ("science", (0, -90, 359.99, 90), np.array([532, 579])),
        ("science", (-180, -90, 180, 90), np.array([532, 579])),
        ("science", (0, -90, 360, 90), np.array([532, 579])),
        ("calval", (-180, -90, 179, 90), np.array([25, 26])),
        ("calval", (0, -90, 359, 90), np.array([25, 26])),
        ("calval", (-130, -50, -90, 50), np.array([26])),
        ("calval", (230, -50, 270, 50), np.array([26])),
    ],
)
def test_query_half_orbits_intersect(phase, bbox, result_passes):
    passes = query_half_orbits_intersect(bbox, phase)
    assert np.array_equal(np.stack(passes.pass_number), result_passes)


@pytest.mark.parametrize(
    "phase, bbox",
    [
        ("science", (0, 0, 0, 0)),
        ("science", (250, -10, 270, 10)),
        ("science", (-110, -10, -90, 10)),
        ("calval", (0, 0, 0, 0)),
        ("calval", (0, 0, 1, 1)),
    ],
)
def test_query_half_orbits_intersect_none(phase, bbox):
    passes = query_half_orbits_intersect(bbox, phase)
    assert passes.empty
