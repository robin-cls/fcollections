from __future__ import annotations

import dataclasses as dc
import importlib.resources
import typing as tp

import numpy as np
from jinja2 import Environment, FileSystemLoader

if tp.TYPE_CHECKING:  # pragma: no cover
    import netCDF4 as nc4


@dc.dataclass
class GroupMetadata:
    """Metadata for a group of variables.

    A dataset may be organized as a simple set of variables, or adopt a
    more complex tree-like structure. This dataclass reflects the most
    complex case where we can have an indefinite number of nesting
    levels. The simplest case (no concept of groups) is naturally well-
    contained within this model.
    """

    name: str
    """Name of the group (can be set to '/' when no nesting is needed)."""
    variables: list[VariableMetadata]
    """List of variables contained in the group."""
    subgroups: list[GroupMetadata]
    """Nested groups."""
    attributes: dict[str, str]
    """Dictionary of attributes specific to the group."""
    dimensions: dict[str, int]
    """Name and size of the dimensions contained in the group."""

    def _repr_html_(self):
        return _render_html(self.flatten())

    def flatten(self) -> list[dict[str, tp.Any]]:
        """Flatten the tree structure to a dictionary.

        Group names will be converted to absolute paths with '/' separator.

        Returns
        -------
        :
            A dictionary containing all the groups, with keys containing paths
            linked to the tree structure
        """
        root = dc.asdict(self)
        visitor = []
        _collect(visitor, root)
        return visitor

    def nodes(self, path: str) -> list[GroupMetadata]:
        """Walk the metadata tree and retrieves the nodes along a given path.

        Parameters
        ----------
        path
            Absolute path for the node to find. The path separator is '/'. For
            example, a path [root, first_level, second_level] can be given as
            root/first_level/second_level or /root/first_level/second_level (the
            prepending '/' will be stripped)

        Returns
        -------
        :
            List of nodes that are part of the path, starting with the root node
            and ending with the last node of the path

        Raises
        ------
        ValueError
            In case nodes are missing in the path
        """
        current = self

        yield current
        for group_name in path.lstrip("/").split("/"):
            group_names = [g.name for g in current.subgroups]
            ii = group_names.index(group_name)
            current = current.subgroups[ii]
            yield current

    def apply(self, callable: tp.Callable[[GroupMetadata]]):
        """Apply a callable to the metadata tree.

        Useful to modify the tree in place/

        Parameters
        ----------
        callable
            The function to apply to each node
        """
        callable(self)
        for subgroup in self.subgroups:
            subgroup.apply(callable)


def _collect(visitor: list[dict(str, tp.Any)], node: dict(str, tp.Any), path: str = ""):
    # visitor is modified in place
    path = path + node["name"]
    node["name"] = path

    children = node.pop("subgroups")

    # Flatten attributes dictionnary in variables
    # This will allow for a simpler table display
    for variable in node["variables"]:
        for k, v in variable["attributes"].items():
            variable[k] = v
        del variable["attributes"]

    visitor.append(node)
    for child in children:
        _collect(visitor, child, path)


def _render_html(groups: dict[str, tp.Any]) -> str:
    # Render a groups metadata. The group hierarchy is flattened to allow easier
    # reading from the user
    assets = importlib.resources.files("fcollections.core").joinpath("assets")
    env = Environment(loader=FileSystemLoader(assets))
    template = env.get_template("template.jinja")
    css = assets.joinpath("style.css").read_text()

    return template.render(groups=groups, css=css)


@dc.dataclass
class VariableMetadata:
    """Metadata of a variable."""

    name: str
    """Name of the variable."""
    dtype: np.dtype
    """Type of the variable as a numpy dtype."""
    dimensions: tuple[str, ...]
    """Dimensions' names."""
    attributes: dict[str, str]
    """Dictionary of attributes specific to the variable."""

    def __post_init__(self):
        if not isinstance(self.dtype, np.dtype):
            self.dtype = np.dtype(self.dtype)


def group_metadata_from_netcdf(nds: nc4.Dataset) -> GroupMetadata:
    """Extract metadata from a netcdf dataset.

    Parameters
    ----------
    nds
        The netcdf dataset from which we want the metadata

    Returns
    -------
    :
        The associated GroupMetadata
    """
    return GroupMetadata(
        name=nds.name,
        attributes={x: nds.getncattr(x) for x in nds.ncattrs()},
        dimensions={d.name: d.size for d in nds.dimensions.values()},
        variables=[
            VariableMetadata(
                v.name, v.dtype, v.dimensions, {x: v.getncattr(x) for x in v.ncattrs()}
            )
            for v in nds.variables.values()
        ],
        subgroups=[group_metadata_from_netcdf(group) for group in nds.groups.values()],
    )
