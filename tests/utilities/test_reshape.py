import numpy as np
import pytest

from fcollections.utilities.reshape import slice_along_axis


@pytest.fixture
def data():
    return np.random.random((10, 20, 5))


def test_slice_along_axis(data):
    sliced = slice_along_axis(data, 0, slice(2, 5))
    assert np.array_equal(data[2:5], sliced)
    # The whole goal of slice_along_axis is to avoid copy and get a view instead
    assert sliced.base is not None

    sliced = slice_along_axis(data, 1, slice(None, 15, 2))
    assert np.array_equal(data[:, :15:2], sliced)
    assert sliced.base is not None

    sliced = slice_along_axis(data, 2, slice(3, 6))
    assert np.array_equal(data[:, :, 3:], sliced)
    assert sliced.base is not None
