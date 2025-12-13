import typing as tp

import bs4
import netCDF4 as nc4
import numpy as np
import pytest
import yaml

from fcollections.core._metadata import (
    GroupMetadata,
    VariableMetadata,
    _render_html,
    group_metadata_from_netcdf,
)


@pytest.fixture
def groups() -> GroupMetadata:
    return GroupMetadata(
        "/",
        variables=[],
        subgroups=[
            GroupMetadata(
                "group1",
                variables=[
                    VariableMetadata(
                        "var1", np.float64, ("x",), dict(comment="a random var")
                    ),
                    VariableMetadata(
                        "var2", np.int32, ("x", "y"), dict(comment="another random var")
                    ),
                ],
                attributes={},
                dimensions=dict(x=10, y=5),
                subgroups=[],
            )
        ],
        attributes=dict(foo=1, bar="baz"),
        dimensions={},
    )


@pytest.fixture
def flattened() -> dict[str, tp.Any]:
    expected = yaml.safe_load(
        """
        - name: /
          variables: []
          attributes:
            foo: 1
            bar: baz
          dimensions: {}
        - name: /group1
          variables:
          - name: var1
            dtype: f8
            dimensions: ['x']
            comment: a random var
          - name: var2
            dtype: i4
            dimensions: ['x', 'y']
            comment: another random var
          attributes: {}
          dimensions:
            x: 10
            y: 5
    """
    )
    for x in [expected[1]["variables"][0], expected[1]["variables"][1]]:
        x["dimensions"] = tuple(x["dimensions"])
    return expected


@pytest.fixture
def netcdf_dataset(tmp_path):
    file = tmp_path / "dummy.nc"
    with nc4.Dataset(file, mode="w") as nds:

        root = nds.createGroup("/")
        setattr(root, "foo", 1)
        setattr(root, "bar", "baz")

        group1 = root.createGroup("group1")
        group1.createDimension("x", 10)
        group1.createDimension("y", 5)

        var1 = group1.createVariable("var1", np.float64, ["x"])
        setattr(var1, "comment", "a random var")
        var2 = group1.createVariable("var2", np.int32, ["x", "y"])
        setattr(var2, "comment", "another random var")

    with nc4.Dataset(file, mode="r") as nds:
        yield nds


def test_flatten(groups: GroupMetadata, flattened: dict[str, tp.Any]):
    assert groups.flatten() == flattened


def test_group_metadata_from_netcdf(netcdf_dataset, groups):
    assert groups == group_metadata_from_netcdf(netcdf_dataset)


def test_render(groups: GroupMetadata):
    # Style sheet has been properly applied
    parsed = bs4.BeautifulSoup(groups._repr_html_(), "html.parser")
    assert len(parsed.style.contents) > 0

    # Test overall structure
    names = [
        "Group: /",
        "Dimensions",
        "Variables",
        "Attributes",
        "Group: /group1",
        "Dimensions",
        "Variables",
        "var1",
        "var2",
        "Attributes",
    ]
    for x, y in zip(parsed.find_all("details"), names):
        assert x.summary.contents[0] == y


def test_variable_normalization():
    # Dtypes should be normalized as an input
    reference = VariableMetadata("x", np.dtype("f8"), tuple(), {})
    assert VariableMetadata("x", "f8", tuple(), {}) == reference
    assert VariableMetadata("x", np.float64, tuple(), {}) == reference
    assert VariableMetadata("x", float, tuple(), {}) == reference


@pytest.fixture
def nested_groups() -> GroupMetadata:
    return GroupMetadata(
        "/",
        variables=[],
        subgroups=[
            GroupMetadata(
                "group1",
                variables=[],
                attributes={},
                dimensions=dict(x=10),
                subgroups=[
                    GroupMetadata(
                        "groupA",
                        variables=[],
                        attributes={},
                        dimensions=dict(y=3),
                        subgroups=[],
                    )
                ],
            ),
            GroupMetadata(
                "group2",
                variables=[],
                attributes={},
                dimensions=dict(x=5),
                subgroups=[
                    GroupMetadata(
                        "groupA",
                        variables=[],
                        attributes={},
                        dimensions=dict(y=6),
                        subgroups=[],
                    )
                ],
            ),
        ],
        attributes={},
        dimensions={},
    )


def test_nodes_error(nested_groups: GroupMetadata):
    with pytest.raises(ValueError):
        list(nested_groups.nodes("/group1/groupB"))


def test_nodes(nested_groups: GroupMetadata):
    expected = [
        nested_groups,
        nested_groups.subgroups[0],
        nested_groups.subgroups[0].subgroups[0],
    ]
    nodes = list(nested_groups.nodes("/group1/groupA"))
    assert expected == nodes


def test_nodes_strip(nested_groups: GroupMetadata):
    assert list(nested_groups.nodes("/group1/groupA")) == list(
        nested_groups.nodes("group1/groupA")
    )


def test_apply(nested_groups: GroupMetadata):

    def _decimate(group: GroupMetadata):
        try:
            group.dimensions["x"] //= 2
        except KeyError:
            # Do nothing
            pass

        try:
            group.dimensions["y"] //= 3
        except KeyError:
            # Do nothing
            pass

    nested_groups.apply(_decimate)
    _, node1, node1A = nested_groups.nodes("/group1/groupA")
    _, node2, node2A = nested_groups.nodes("/group2/groupA")
    assert node1.dimensions["x"] == 5
    assert node2.dimensions["x"] == 2
    assert node1A.dimensions["y"] == 1
    assert node2A.dimensions["y"] == 2
