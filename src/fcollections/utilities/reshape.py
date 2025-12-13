import numpy as np


def slice_along_axis(array: np.ndarray, axis: int, slice_along_axis: slice):
    """Take a slice over a given axis.

    Similar to np.take but produce a view. The counter-part to this is that only
    slices are supported so no advanced indexing.

    Parameters
    ----------
    array
        Array to slice
    axis
        Axis along which the slice will be taken
    slice_along_axis
        Slice definition

    Returns
    -------
    :
        The sliced array
    """
    slices = [slice(None)] * array.ndim
    slices[axis] = slice_along_axis
    return array[tuple(slices)]
