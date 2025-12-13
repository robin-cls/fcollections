import numpy as np
import pytest

from fcollections.geometry import (
    LongitudeConvention,
    StandardLongitudeConvention,
    guess_longitude_convention,
)


def test_invalid_convention():
    with pytest.raises(ValueError):
        LongitudeConvention(-180, 360)


@pytest.mark.parametrize(
    "convention, array, expected_arr",
    [
        ((0, 360), [-180, 179.99], [180, 179.99]),
        ((-180, 180), [0, 359], [0, -1]),
        ((-180, 180), [-180, 180], [-180, 180]),
        ((0, 360), [0, 360], [0, 360]),
        ((-180, 180), [0, 1], [0, 1]),
        ((0, 360), [0, 1], [0, 1]),
        ((-180, 180), [-180, -100, 0, 1, 180], [-180, -100, 0, 1, 180]),
        ((0, 360), [-180, -100, 0, 1, 180], [180, 260, 0, 1, 180]),
        ((-180, 180), [0, 100, 300, 360], [0, 100, -60, 0]),
        ((0, 360), [0, 100, 300, 360], [0, 100, 300, 360]),
        ((-180, 180), [92, 259], [92, -101]),
        ((-180, 180), [118, 285], [118, -75]),
        ((0, 360), [92, 259], [92, 259]),
        ((-180, 180), [150, -100], [150, -100]),
        ((0, 360), [150, -100], [150, 260]),
        ((-180, 180), [-100, 150], [-100, 150]),
        ((0, 360), [-100, 150], [260, 150]),
        ((-180, 180), [-100, -20], [-100, -20]),
        ((0, 360), [-100, -20], [260, 340]),
        # More %360
        ((0, 360), [800, 950, 1000], [80, 230, 280]),
        ((0, 360), [720, 800, 950, 1000, 1079], [0, 80, 230, 280, 359]),
        ((-180, 180), [-540, -400, -360, -200, -181], [-180, -40, 0, 160, 179]),
        ((0, 360), [-540, -400, -360, -200, -181], [180, 320, 0, 160, 179]),
    ],
)
def test_normalize(convention, array, expected_arr):
    conv = LongitudeConvention(*convention)
    arr = conv.normalize(np.array(array))
    assert np.array_equal(arr, np.array(expected_arr))


def test_normalize_inplace():
    convention = StandardLongitudeConvention.CONV_180.value
    reference = np.array([50, 370])
    expected = np.array([50, 10])

    normalized = convention.normalize(reference)
    assert np.array_equal(normalized, expected)
    assert not np.array_equal(normalized, reference)

    convention.normalize(reference, inplace=True)
    assert np.array_equal(normalized, reference)


@pytest.mark.parametrize(
    "convention, array, expected_arr",
    [
        ((-180, 180), [0, 1], [[0, 1]]),
        ((0, 360), [0, 1], [[0, 1]]),
        ((-180, 180), [-180, -100, 0, 1, 180], [[-180, -100, 0, 1, 180]]),
        ((0, 360), [-180, -100, 1, 180], [[180, 260, 360], [0, 1, 180]]),
        ((-180, 180), [0, 100, 300, 360], [[0, 100, 180], [-180, -60, 0]]),
        ((0, 360), [0, 100, 300, 360], [[0, 100, 300, 360]]),
        ((-180, 180), [92, 259], [[92, 180], [-180, -101]]),
        ((-180, 180), [118, 285], [[118, 180], [-180, -75]]),
        ((0, 360), [92, 259], [[92, 259]]),
        ((-180, 180), [150, -100], [[150, 180], [-180, -100]]),
        ((0, 360), [150, -100], [[150, 260]]),
        ((-180, 180), [-100, 150], [[-100, 150]]),
        ((0, 360), [-100, 150], [[260, 360], [0, 150]]),
        ((-180, 180), [-100, -20], [[-100, -20]]),
        ((0, 360), [-100, -20], [[260, 340]]),
    ],
)
def test_normalize_and_split(convention, array, expected_arr):
    conv = LongitudeConvention(*convention)
    arr = conv.normalize_and_split(np.array(array))

    assert np.array_equal(arr[0], np.array(expected_arr[0]))

    if len(arr) > 1:
        assert np.array_equal(arr[1], np.array(expected_arr[1]))


@pytest.mark.parametrize(
    "lon_array, expected_convention",
    [
        (([0, 3, 100, 250]), StandardLongitudeConvention.CONV_360),
        (([0, 360, 1, 10, 20]), StandardLongitudeConvention.CONV_360),
        (([0, 1, 10, 20]), StandardLongitudeConvention.CONV_360),
        (([-180, -12, 0, 180]), StandardLongitudeConvention.CONV_180),
        (([360, 0, 181, 26, 320, 360, 0]), StandardLongitudeConvention.CONV_360),
    ],
)
def test_guess_longitude_convention(lon_array, expected_convention):
    conv_result = guess_longitude_convention(np.array(lon_array))
    assert conv_result == expected_convention


@pytest.mark.parametrize(
    "lon_array",
    [
        ([-12, 0, 3, 100, 250]),
        ([0, 360, 1, 10, 2, 400]),
        ([-181, 0, 1, 10, 20]),
        ([360, 0, 181, 26, 320, 360, -1]),
    ],
)
def test_guess_longitude_convention_error(lon_array):
    with pytest.raises(ValueError):
        guess_longitude_convention(np.array(lon_array))
