from __future__ import annotations

import numpy as np
import pytest
import xarray as xr
from utils import brute_force_geographical_selection, extract_box_from_polygon

from fcollections.implementations.optional._area_selectors import (
    AreaSelector2D,
    SwathAreaSelector,
    TemporalSerieAreaSelector,
    _select_2d_indices_intersect_bounds,
    _select_slices_intersect_bounds,
)


@pytest.mark.parametrize(
    "x_bounds, y_bounds, result",
    [
        ((1, 6), (1, 6), (0, 1)),
        ((1, 6), (5.5, 6), ()),
        ((1, 6), (5, 5), (1,)),
        ((5.5, 6), (1, 6), ()),
        ((3, 4), (2.5, 4.5), (0, 1)),
        ((1, 6), (0, 2), (0,)),
        ((1, 6), (0, 2.5), (0,)),
        ((0, 2), (1, 6), (0,)),
        ((3, 4), (3, 4), ()),
        ((2, 3), (3, 5), (0, 1)),
        # tests circularity in x axis
        ((5, 1), (1, 6), (1,)),
        ((6, 1), (1, 6), ()),
        ((2, 1), (1, 6), (0, 1)),
        ((5, 2), (1, 6), (0, 1)),
        ((5, 4), (1, 6), (0, 1)),
        ((5, 2), (2, 3), (0,)),
        ((5, 2), (4, 5), (1,)),
        ((5, 4), (2, 3), (0,)),
        ((5, 4), (4, 5), (1,)),
    ],
)
def test_select_2d_indices_intersect_bounds(x_bounds, y_bounds, result):
    x_arr = np.array([[2, 3, 4], [3, 4, 5]])
    y_arr = np.array([[3, 2.5, 2], [5, 4.5, 4]])
    (ind_x, _) = _select_2d_indices_intersect_bounds(x_arr, y_arr, x_bounds, y_bounds)
    assert tuple(np.unique(ind_x)) == result


def test_select_2d_indices_intersect_bounds_error():
    x_bounds, y_bounds = (4, 5), (4, 3)
    x_arr = np.array([[2, 3, 4], [3, 4, 5]])
    y_arr = np.array([[3, 2.5, 2], [5, 4.5, 4]])
    with pytest.raises(ValueError):
        _select_2d_indices_intersect_bounds(x_arr, y_arr, x_bounds, y_bounds)


class Test_select_slice_intersect_bounds:

    @pytest.mark.parametrize(
        "bounds, ind_start, result",
        [
            ((1, 2), 0, [(3, 5)]),
            ((1, 2), 2, [(5, 7)]),
            ((1, 1.5), 0, [(3, 4)]),
            ((-3, 3), 0, [(0, 5)]),
            ((-3, 2), 0, [(0, 5)]),
            ((-3, 0), 0, [(0, 3)]),
            ((-3, -2), 0, [(0, 1)]),
            ((-2, 3), 0, [(0, 5)]),
            ((0, 3), 0, [(2, 5)]),
            ((2, 2), 0, [(4, 5)]),
            ((2, 3), 0, [(4, 5)]),
            ((-1, 1), 0, [(1, 4)]),
            ((-2, -2), 0, [(0, 1)]),
            # tests circularity
            ((1, 0), 0, [(0, 3), (3, 5)]),
            (
                (2, -2),
                0,
                [
                    (0, 1),
                    (4, 5),
                ],
            ),
            (
                (2, -0.5),
                0,
                [
                    (0, 2),
                    (4, 5),
                ],
            ),
        ],
    )
    def test_nominal(self, bounds, ind_start, result):
        array = np.array([-2, -1, 0, 1, 2])
        sl = _select_slices_intersect_bounds(array, bounds, ind_start)
        assert sl == [slice(*r) for r in result]

    @pytest.mark.parametrize(
        "bounds, ind_start, result",
        [
            ((1, 2), 0, [(2, 4)]),
            ((0, 5), 0, [(0, 5)]),
            ((2, 1), 0, [(2, 4)]),
        ],
    )
    def test_unordered(self, bounds, ind_start, result):
        array = np.array([4, 3, 2, 1, 0])
        sl = _select_slices_intersect_bounds(array, bounds, ind_start)
        assert sl == [slice(*r) for r in result]

    @pytest.mark.parametrize(
        "array, bounds",
        [
            ([], (0, 1)),
            ([0, 1, 2], (-10, -1)),
            ([0, 1, 2], (3, 10)),
        ],
    )
    def test_none_cases(self, array, bounds):
        assert _select_slices_intersect_bounds(np.array(array), bounds) == [None]


class Test_AreaSelector2D:

    @pytest.mark.parametrize(
        "longitude, latitude", [("bad_lon", "latitude"), ("longitude", "bad_lat")]
    )
    def test_bad_lonlat(self, l4_ssha_dataset_180_180, longitude, latitude):
        """Test apply with bad longitude and latitude names."""
        selector = AreaSelector2D(longitude=longitude, latitude=latitude)
        with pytest.raises(KeyError):
            selector.apply(l4_ssha_dataset_180_180, (0, 1, 0, 1))

    @pytest.mark.parametrize(
        "bbox, lon_values, lat_values",
        [
            ((1, 1, 2, 2), [1, 2], [1, 2]),
            ((-2, -2, 2, 2), [-2, -1, 0, 1, 2], [-2, -1, 0, 1, 2]),
            ((-10, -10, 10, 10), [-2, -1, 0, 1, 2], [-2, -1, 0, 1, 2]),
            ((1, -1, 3, 3), [1, 2], [-1, 0, 1, 2]),
            ((0, -2, 0, 2), [0], [-2, -1, 0, 1, 2]),
            ((-2, 0, 2, 0), [-2, -1, 0, 1, 2], [0]),
            ((0, 0, 1.5, 1.5), [0, 1], [0, 1]),
            ((-3, -2, -2, -2), [-2], [-2]),
            ((2, 1, 3, 1), [2], [1]),
            ((-3, -3, -4, -4), [], []),
            ((-3, -3, 3, -3), [], []),
            ((-3, -3, -3, 3), [], []),
            ((-3, 3, -1, 3), [], []),
            ((1, 3, 3, 3), [], []),
            ((1, -3, 3, -3), [], []),
            ((-180, -90, 180, 90), [-2, -1, 0, 1, 2], [-2, -1, 0, 1, 2]),
            ((-179, -90, 179, 90), [-2, -1, 0, 1, 2], [-2, -1, 0, 1, 2]),
            # tests circularity
            ((-1, 1, -2, 1), [-2, -1, 0, 1, 2], [1]),
            ((-3, -2, -5, 2), [-2, -1, 0, 1, 2], [-2, -1, 0, 1, 2]),
            ((1, 1, -3, 4), [1, 2], [1, 2]),
            ((180, -90, -180, 90), [], []),
            ((179, -90, -179, 90), [], []),
        ],
    )
    def test_apply_180_180(self, l4_ssha_dataset_180_180, bbox, lon_values, lat_values):
        """Test apply with a bbox intersecting the dataset."""
        selector = AreaSelector2D()
        ds = selector.apply(l4_ssha_dataset_180_180, bbox)
        assert np.array_equal(ds.longitude.values, np.array(lon_values))
        assert np.array_equal(ds.latitude.values, np.array(lat_values))

    @pytest.mark.parametrize(
        "bbox, lon_values, lat_values",
        [
            ((0, 0, 4, 4), [0, 1, 2], [2, 1, 0]),
            ((-2, -2, 2, 2), [-2, -1, 0, 1, 2], [2, 1, 0, -1, -2]),
            ((-10, -10, 10, 10), [-2, -1, 0, 1, 2], [2, 1, 0, -1, -2]),
            ((1, -1, 3, 3), [1, 2], [2, 1, 0, -1]),
            ((0, -2, 0, 2), [0], [2, 1, 0, -1, -2]),
            ((-2, 0, 2, 0), [-2, -1, 0, 1, 2], [0]),
            ((0, 0, 1.5, 1.5), [0, 1], [1, 0]),
            ((-3, -2, -2, -2), [-2], [-2]),
            ((2, 1, 3, 1), [2], [1]),
            ((-3, -3, -4, -4), [], []),
            ((-3, -3, 3, -3), [], []),
            ((-3, -3, -3, 3), [], []),
            ((-3, 3, -1, 3), [], []),
            ((1, 3, 3, 3), [], []),
            ((1, -3, 3, -3), [], []),
            ((-180, -90, 180, 90), [-2, -1, 0, 1, 2], [2, 1, 0, -1, -2]),
            ((-179, -90, 179, 90), [-2, -1, 0, 1, 2], [2, 1, 0, -1, -2]),
            # tests circularity
            ((-1, 1, -2, 1), [-2, -1, 0, 1, 2], [1]),
            ((-3, -2, -5, 2), [-2, -1, 0, 1, 2], [2, 1, 0, -1, -2]),
            ((1, 1, -3, 4), [1, 2], [2, 1]),
            ((180, -90, -180, 90), [], []),
            ((179, -90, -179, 90), [], []),
        ],
    )
    def test_apply_desc_lat_180_180(
        self, l4_ssha_dataset_reversed_lat, bbox, lon_values, lat_values
    ):
        """Test apply with a bbox intersecting the dataset."""
        selector = AreaSelector2D()
        ds = selector.apply(l4_ssha_dataset_reversed_lat, bbox)
        assert np.array_equal(ds.longitude.values, np.array(lon_values))
        assert np.array_equal(ds.latitude.values, np.array(lat_values))

    @pytest.mark.parametrize(
        "bbox, lon_values, lat_values",
        [
            ((-2, -2, 2, 2), [0, 1, 2, 358, 359], [1, 2]),
            ((-10, -10, 10, 10), [0, 1, 2, 358, 359], [1, 2]),
            ((0, -2, 0, 2), [0], [1, 2]),
            ((-2, 0, 2, 1), [0, 1, 2, 358, 359], [1]),
            ((-2, 0, -2, 1), [358], [1]),
            ((-3, 3, -1, 2), [358, 359], [2]),
            ((-1, 1, 1, 1), [0, 1, 359], [1]),
            ((300, 1, 360, 2), [358, 359], [1, 2]),
            ((0, -90, 360, 90), [0, 1, 2, 358, 359], [1, 2]),
            # tests circularity in x axis
            ((1, 1, 0, 1), [0, 1, 2, 358, 359], [1]),
            ((359, 1, 358, 1), [0, 1, 2, 358, 359], [1]),
            ((-1, 1, -2, 1), [0, 1, 2, 358, 359], [1]),
            ((357, 1, 355, 4), [0, 1, 2, 358, 359], [1, 2]),
            ((360, -90, 359.5, 90), [0, 1, 2, 358, 359], [1, 2]),
            ((-3, 1, -5, 4), [0, 1, 2, 358, 359], [1, 2]),
            ((3, 1, 0, 4), [0, 358, 359], [1, 2]),
        ],
    )
    def test_apply_0_360(self, l4_ssha_dataset_0_360, bbox, lon_values, lat_values):
        """Test apply with a bbox intersecting the dataset."""
        selector = AreaSelector2D(longitude="lon", latitude="lat")
        ds = selector.apply(l4_ssha_dataset_0_360, bbox)
        assert np.array_equal(ds.lon.values, np.array(lon_values))
        assert np.array_equal(ds.lat.values, np.array(lat_values))


class Test_SwathAreaSelector:

    @pytest.mark.parametrize(
        "longitude, latitude", [("bad_lon", "latitude"), ("longitude", "bad_lat")]
    )
    def test_bad_lonlat(
        self, l2_lr_ssh_basic_dataset: xr.Dataset, longitude: str, latitude: str
    ):
        """Test apply with bad longitude and latitude names."""
        selector = SwathAreaSelector(longitude=longitude, latitude=latitude)
        with pytest.raises(KeyError):
            selector.apply(l2_lr_ssh_basic_dataset, (0, 0, 1, 1))

    @pytest.mark.parametrize("latitude", [-75, -30, 0, 30, 75])
    def test_apply(self, l2_lr_ssh_basic_dataset: xr.Dataset, latitude: float):
        """Test apply with a bbox intersecting the dataset."""
        # Pass in the reference dataset
        pass_number = 25
        # Take a box sufficiently big to account for the difference between the
        # trajectory from the polygon and the trajectory in the dataset built
        # form an approximated formulae
        box_size = 5
        bbox = extract_box_from_polygon(pass_number, box_size, latitude)
        reference = brute_force_geographical_selection(l2_lr_ssh_basic_dataset, *bbox)
        assert reference.num_lines.size > 0
        assert reference.num_lines.size < l2_lr_ssh_basic_dataset.num_lines.size

        selector = SwathAreaSelector()
        ds = selector.apply(l2_lr_ssh_basic_dataset, bbox)

        assert reference == ds

    @pytest.mark.parametrize("latitude", [-75, -30, 0, 30, 75])
    def test_apply_circular(self, l2_lr_ssh_basic_dataset: xr.Dataset, latitude: float):
        """Test apply with a bbox intersecting the dataset."""
        # Pass in the reference dataset
        pass_number = 25
        box_size = 5
        bbox = extract_box_from_polygon(pass_number, box_size, latitude)
        reference = brute_force_geographical_selection(l2_lr_ssh_basic_dataset, *bbox)
        assert reference.num_lines.size > 0
        assert reference.num_lines.size < l2_lr_ssh_basic_dataset.num_lines.size

        selector = SwathAreaSelector()
        bbox = bbox[0], bbox[1], bbox[2] - 360, bbox[3]
        ds = selector.apply(l2_lr_ssh_basic_dataset, bbox)

        assert reference == ds

    @pytest.mark.parametrize("bbox", [(-180, -90, 180, 90), (-179, -90, 179, 90)])
    def test_apply_global(
        self,
        l2_lr_ssh_basic_dataset: xr.Dataset,
        bbox: tuple[float, float, float, float],
    ):
        selector = SwathAreaSelector()
        ds = selector.apply(l2_lr_ssh_basic_dataset, bbox)

        assert ds == l2_lr_ssh_basic_dataset

    @pytest.mark.parametrize("latitude", [-75, -30, 0, 30, 75])
    def test_apply_box_too_small(
        self, l2_lr_ssh_basic_dataset: xr.Dataset, latitude: float
    ):
        """Test apply with a small bbox with no data inside."""
        selector = SwathAreaSelector()

        pass_number = 25  # Pass in the reference dataset
        box_size = 0.1  # This box is too small and will not capture any points
        bbox = extract_box_from_polygon(pass_number, box_size, latitude)
        ds = selector.apply(l2_lr_ssh_basic_dataset, bbox)
        assert ds.sizes["num_lines"] == 0

    @pytest.mark.parametrize("latitude", [-75, -30, 0, 30, 75])
    def test_apply_box_outside(
        self, l2_lr_ssh_basic_dataset: xr.Dataset, latitude: float
    ):
        """Test apply with a small bbox with no data inside."""
        selector = SwathAreaSelector()

        # Science pass, completely unrelated to the calval pass 25 expected in the input dataset
        pass_number = 532
        box_size = 5
        bbox = extract_box_from_polygon(pass_number, box_size, latitude, "science")
        ds = selector.apply(l2_lr_ssh_basic_dataset, bbox)
        assert ds.sizes["num_lines"] == 0

    @pytest.mark.parametrize("bbox", [(180, -90, -180, 90), (179, -90, -179, 90)])
    def test_apply_bad_box(self, l2_lr_ssh_basic_dataset: xr.Dataset, bbox):
        """Test apply with a bbox where lon_min = lon_max."""
        selector = SwathAreaSelector()
        ds = selector.apply(l2_lr_ssh_basic_dataset, bbox)
        assert ds.sizes["num_lines"] == 0

    def test_apply_unknown_convention(self):
        """Test apply with an input dataset without convention on
        longitudes."""
        selector = SwathAreaSelector()

        bbox = -30, -20, 30, 20
        ds = xr.Dataset(
            data_vars={
                # This monotonic sequence will not be monotonic anymore after a
                # convention change. The selector should be robust to this.
                # In CONV_360: [30, 160, 310, 340, 20, 50, 340]
                # In CONV_180: [30, 160, -50, -20, 20, 50, -20]
                "longitude": (
                    ("num_lines", "num_pixels"),
                    np.array([[-330, -200, -50, -20, 20, 50, 340]]).T,
                ),
                "latitude": (
                    ("num_lines", "num_pixels"),
                    np.array([[0, 0, 0, 0, 0, 0, 0]]).T,
                ),
            }
        )
        ds_actual = selector.apply(ds, bbox)
        ds_expected = ds.isel(num_lines=[0, 3, 4, 6])
        xr.testing.assert_identical(ds_actual, ds_expected)


class Test_TemporalSerieAreaSelector:

    @pytest.mark.parametrize(
        "longitude, latitude", [("bad_lon", "latitude"), ("longitude", "bad_lat")]
    )
    def test_bad_lonlat(self, l3_nadir_dataset_0_360, longitude, latitude):
        """Test apply with bad longitude and latitude names."""
        selector = TemporalSerieAreaSelector(longitude=longitude, latitude=latitude)
        with pytest.raises(KeyError):
            selector.apply(l3_nadir_dataset_0_360, (0, 0, 1, 1))

    @pytest.mark.parametrize(
        "bbox, lon_values, lat_values",
        [
            ((-10, -10, 0.5, 0.5), [], []),
            ((3, 3, 5, 7), [], []),
            ((2, 2, 3, 3), [2], [2]),
            ((1, 1, 3, 3), [1, 2], [1, 2]),
            ((1.5, 1.5, 360, 2), [2], [2]),
            ((1.5, 1.5, 360, 3), [2, 358], [2, 3]),
            ((0, 1, 360, 1), [1], [1]),
            ((300, 3, 360, 4), [358, 359], [3, 4]),
            ((0, -90, 360, 90), [1, 2, 358, 359], [1, 2, 3, 4]),
            # tests circularity in x axis
            ((-1, 1, -2, 1), [1], [1]),
            ((-3, 1, -5, 4), [1, 2, 358, 359], [1, 2, 3, 4]),
            ((3, 1, 0, 4), [358, 359], [3, 4]),
            ((360, -90, 0, 90), [], []),
        ],
    )
    def test_apply_0_360(self, l3_nadir_dataset_0_360, bbox, lon_values, lat_values):
        """Test apply with a bbox intersecting the dataset."""
        selector = TemporalSerieAreaSelector()
        ds = selector.apply(l3_nadir_dataset_0_360, bbox)
        assert np.array_equal(ds.longitude.values, np.array(lon_values))
        assert np.array_equal(ds.latitude.values, np.array(lat_values))

    @pytest.mark.parametrize(
        "bbox, lon_values, lat_values",
        [
            ((-10, -10, -3, -3), [], []),
            ((3, 3, 5, 7), [], []),
            ((1.5, 1.5, 10, 3), [2], [2]),
            ((0, 1, 10, 1), [1], [1]),
            ((-2, -1, 1, 1), [-1, 0, 1], [-1, 0, 1]),
            ((-180, -90, 180, 90), [-1, 0, 1, 2], [-1, 0, 1, 2]),
            ((-179, -90, 179, 90), [-1, 0, 1, 2], [-1, 0, 1, 2]),
            # tests circularity in x axis
            ((-1, 1, -2, 1), [1], [1]),
            ((-3, -2, -5, 2), [-1, 0, 1, 2], [-1, 0, 1, 2]),
            ((1, 1, -3, 4), [1, 2], [1, 2]),
            ((180, -90, -180, 90), [], []),
            ((179, -90, -179, 90), [], []),
        ],
    )
    def test_apply_180_180(
        self, l3_nadir_dataset_180_180, bbox, lon_values, lat_values
    ):
        """Test apply with a bbox intersecting the dataset."""
        selector = TemporalSerieAreaSelector()
        ds = selector.apply(l3_nadir_dataset_180_180, bbox)
        assert np.array_equal(ds.longitude.values, np.array(lon_values))
        assert np.array_equal(ds.latitude.values, np.array(lat_values))
