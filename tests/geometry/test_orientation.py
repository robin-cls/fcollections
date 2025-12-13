from __future__ import annotations

import numpy as np
import pytest
import sympy as sp

from fcollections.geometry import rotate_derivatives, rotate_vector, track_orientation


@pytest.mark.parametrize(
    "x, y, theta, X_expected, Y_expected",
    [
        (1, 0, np.pi / 4, 1 / np.sqrt(2), -1 / np.sqrt(2)),
        (0, 1, np.pi / 4, 1 / np.sqrt(2), 1 / np.sqrt(2)),
        (1 / np.sqrt(2), 1 / np.sqrt(2), -np.pi / 4, 0, 1),
        (1, 0, np.pi / 2, 0, -1),
        (1, 0, 3 * np.pi / 2, 0, 1),
        (1 / np.sqrt(2), np.sqrt(2), np.pi / 4, 1.5, 0.5),
    ],
)
def test_rotate_vector(
    x: float, y: float, theta: float, X_expected: float, Y_expected: float
):
    X, Y = rotate_vector(x, y, theta)
    assert np.isclose(X, X_expected)
    assert np.isclose(Y, Y_expected)
    assert np.isclose(x**2 + y**2, X**2 + Y**2)


def test_rotate_derivatives():

    xx, yy = sp.symbols("x, y")
    vx = xx**2 + 2 * xx + 2 * yy**2 - 2 * xx * yy - 7 * yy + 4
    vy = 2 * xx**2 - 3 * xx - yy**2 + 1.5 * xx * yy + yy + 10

    dvx_dx = sp.Derivative(vx, xx).doit()
    dvx_dy = sp.Derivative(vx, yy).doit()
    dvy_dx = sp.Derivative(vy, xx).doit()
    dvy_dy = sp.Derivative(vy, yy).doit()

    step = 0.5
    X = np.arange(-10, 10, step)
    Y = np.arange(-10, 10, step)
    Y, X = np.meshgrid(Y, X)

    x, y = rotate_vector(X, Y, -np.pi / 4)

    dvx_dx_ref = sp.lambdify((xx, yy), dvx_dx)(x, y)
    dvx_dy_ref = sp.lambdify((xx, yy), dvx_dy)(x, y)
    dvy_dx_ref = sp.lambdify((xx, yy), dvy_dx)(x, y)
    dvy_dy_ref = sp.lambdify((xx, yy), dvy_dy)(x, y)

    vx = sp.lambdify((xx, yy), vx)(x, y)
    vy = sp.lambdify((xx, yy), vy)(x, y)
    vX, vY = rotate_vector(vx, vy, np.pi / 4)

    dvX_dX, dvX_dY = np.gradient(vX)
    dvY_dX, dvY_dY = np.gradient(vY)

    dvX_dX /= step
    dvX_dY /= step
    dvY_dY /= step
    dvY_dX /= step

    dvx_dx, dvy_dy, dvx_dy, dvy_dx = rotate_derivatives(
        dvX_dX, dvY_dY, dvX_dY, dvY_dX, np.pi / 4
    )

    assert np.allclose(dvx_dx_ref[1:-1, 1:-1], dvx_dx[1:-1, 1:-1])
    assert np.allclose(dvx_dy_ref[1:-1, 1:-1], dvx_dy[1:-1, 1:-1])
    assert np.allclose(dvy_dx_ref[1:-1, 1:-1], dvy_dx[1:-1, 1:-1])
    assert np.allclose(dvy_dy_ref[1:-1, 1:-1], dvy_dy[1:-1, 1:-1])


@pytest.mark.parametrize(
    "latitudes, longitudes, expected_angle",
    [
        ([0, 1], [0, 0], np.pi / 2),
        ([0, -1], [0, 0], -np.pi / 2),
        ([0, 0], [0, 1], 0),
        ([0, 0], [0, -1], np.pi),
        ([0, 1], [0, 1], np.pi / 4),
        ([0, 1], [0, -1], 3 * np.pi / 4),
        ([0, -1], [0, 1], -np.pi / 4),
        ([0, -1], [0, -1], -3 * np.pi / 4),
    ],
    ids=[
        "northward",
        "southward",
        "eastward",
        "westward",
        "northeastward",
        "northwestward",
        "southeastward",
        "southwestward",
    ],
)
def test_track_orientation(
    latitudes: list[int], longitudes: list[int], expected_angle: float
):
    angle = track_orientation(latitudes, longitudes)
    assert angle[0] == expected_angle
