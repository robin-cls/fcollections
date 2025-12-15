from __future__ import annotations

import abc
import dataclasses as dc
import logging
import typing as tp

import fsspec

logger = logging.getLogger(__name__)

from fcollections.core import Layout


class INode(abc.ABC):
    """Representation of a file system path.

    Parameters
    ----------
    name
        Name of the node. Not to be confused with the full path that should be
        contained in the info parameter
    info
        Additional information. ``name`` - representing the full path - is
        expected to be in this parameter. Other information will depend on the
        ``fsspec`` implementations
    level
        Nesting level of the current node with respect to the tree root
    """

    def __init__(self, name: str, info: dict[str, tp.Any], level: int):
        self.name = name
        self.info = info
        self.level = level

    @abc.abstractmethod
    def accept(self, visitor: LayoutVisitor) -> VisitResult:
        """Accept a visitor.

        This method should trigger operations in the visitor. The visitor
        computes the desired result, and the node is responsible for emitting
        said-result to the walk operation.

        Returns
        -------
        :
            The visit result

        See Also
        --------
        walk
            Walk operation handling the tree traversal
        """

    @abc.abstractmethod
    def children(self) -> tp.Iterator[INode]:
        """List child nodes.

        Returns
        -------
        :
            The child nodes, either files or folders
        """


class FileNode(INode):
    """File node of a file system tree."""

    def accept(self, visitor: LayoutVisitor) -> VisitResult:
        return visitor.visit_file(self)

    def children(self) -> tp.Iterator[INode]:
        """List child nodes.

        Returns
        -------
        :
            An empty list (files have no children)
        """
        return []


class DirNode(INode):
    """Directory node of a file system tree.

    Parameters
    ----------
    name
        Name of the node. Not to be confused with the full path that should be
        contained in the info parameter
    info
        Additional information. The entry ``name`` - representing the full path
        - is expected to be in this parameter. Other information will depend on
        the ``fsspec`` implementation
    level
        Nesting level of the current node with respect to the tree root
    fs
        File system hosting the node. Useful to list the children
    """

    def __init__(self, name, info, fs: fsspec.AbstractFileSystem, level: int):
        super().__init__(name, info, level)
        self.fs = fs
        self._children: list[INode] | None = None

    def accept(self, visitor: LayoutVisitor) -> VisitResult:
        return visitor.visit_dir(self)

    def children(self) -> tp.Iterable[INode]:
        # Cache children computation to avoid expensive relisting and ensure
        # that one path on the filesystem will be represented by the same node
        if self._children is None:
            self._children = list(self._compute_children())
        return self._children

    def _compute_children(self) -> tp.Iterator[INode]:
        # return list of FileNode or DirNode instances
        # Block of code extracted from fsspec and simplified (no topbottom
        # option)
        path = self.fs._strip_protocol(self.info["name"])

        try:
            listing = self.fs.ls(path, detail=True)
        except (FileNotFoundError, OSError):
            return

        for info in listing:
            # each info name must be at least [path]/part , but here
            # we check also for names like [path]/part/
            pathname = info["name"].rstrip("/")
            name = pathname.rsplit("/", 1)[-1]
            if info["type"] == "directory" and pathname != path:
                # do not include "self" path
                yield DirNode(name, info, self.fs, self.level + 1)
            elif pathname == path:
                # file-like with same name as give path
                # consequence of virtual directories in cloud object stores
                yield FileNode("", info, self.level + 1)
            else:
                yield FileNode(name, info, self.level + 1)


@dc.dataclass(frozen=True)
class VisitResult:
    """Result of a visit.

    The result type is defined by the :class:`IVisitor` implementations.

    Additional information related to semantic definition contained in layouts
    (:class:`Layout`) is given for further advancement of the visitors.

    Tree traversal can also use exploration hints given by the visitors
    decide if the current branch should be explored.

    See Also
    --------
    walk
        Handle tree traversal
    """

    explore_next: bool
    """True if we should continue to explore the current branch."""
    payload: tp.Any | None = None
    """Post processing result of a node by the visitor."""
    surviving_layouts: list[Layout] = dc.field(default_factory=list)
    """:class:`LayoutVisitor` only, used to know which semantic is still valid
    for the current branch."""


class IVisitor(abc.ABC):
    """Visitor processing an :class:`INode`.

    Visitors interpret a node and return information from it. It is up
    to the implementation to define which information it can get from
    the node. Some implementations will only return the node path, other
    will try to interpret it using semantics' definitions.

    An important characteristic of the visitor is its ability to advance
    from a previous visit result. This gives flexibility to implement
    specific states during the tree traversal.

    Additionnal metadata about the visit are also returned by the
    visitor. This information should be used for tree traversal and
    visitor advancement only, and not returned by the walk operation.
    """

    @abc.abstractmethod
    def visit_dir(self, dir_node: DirNode) -> VisitResult:
        """Visits a directory node.

        Returns
        -------
        :
            Node information and visit metadata.
        """

    @abc.abstractmethod
    def visit_file(self, file_node: DirNode) -> VisitResult:
        """Visits a file node.

        Returns
        -------
        :
            Node information and visit metadata.
        """

    @abc.abstractmethod
    def advance(self, result: VisitResult) -> IVisitor:
        """Advance the visitor.

        The advancement can either return a reference or a copy of the visitor.
        If a per-branch state is needed, it is advised to return a copy.

        Parameters
        ----------
        result
            Previous result of a visit. Originally intended to be the visit
            result of the parent node.

        Returns
        -------
        :
            The current visitor or a copy with a modified state
        """


class StandardVisitor(IVisitor):
    """Visitor for producing the equivalent of
    :meth:`fsspec.spec.AbstractFileSystem.walk`.

    The useful information is a tuple (root, dirs, files) that mimics
    the standard output of a walk operation.

    No additionnal metadata related to the visit itself is returned.
    """

    def visit_dir(self, dir_node: DirNode) -> VisitResult:
        dirs = []
        files = []
        for x in dir_node.children():
            if isinstance(x, DirNode):
                dirs.append(x.name)
            else:
                files.append(x.name)
        return VisitResult(True, (dir_node.info["name"], dirs, files))

    def visit_file(self, file_node: DirNode) -> VisitResult:
        # No payload in visit_file
        return VisitResult(False)

    def advance(self, result: VisitResult) -> StandardVisitor:
        # Visitor should advance without copy, duplication or state alteration
        return self


class LayoutVisitor(IVisitor):
    """Visitor with node interpretation and branch exploration hints.

    The layouts will try to interpret a node and get a record of structured
    information. Layouts also include filters that are applied to give a hint
    about tree exploration: if all layouts exclude the current node, exploration
    should not continue.

    Parameters
    ----------
    layouts
        Semantic definitions for interpreting and testing node meanings
    """

    def __init__(self, layouts: list[Layout]):
        self.layouts = layouts

    def visit_dir(self, dir_node: DirNode) -> VisitResult:
        """Visits a directory node.

        The directory node path is parsed into a structured node. If none of the
        layouts is able to parse the node, it means we are in uncharted
        territory: tree traversal hint in the visit result will state we should
        not continue exploring.

        In addition, layout filters are applied on the node information. If all
        layouts exclude the node, it means no node of interest are in this
        branch: we want to terminate the current branch exploration as soon as
        possible to speed up the walk operation.

        Multiple layouts means multiple semantics are possible. This is the case
        in a heterogeneous folder. When exploring a branch, some layouts may not
        match the branch semantic. These are pruned as soon as possible, but
        only for the current branch.

        Returns
        -------
        :
            Node information and visit metadata. The visit metadata includes a
            tree traversal hint for further exploration, and the surviving
            layouts that match the current branch
        """
        logger.debug("Visiting folder %s", dir_node.info["name"])
        if dir_node.level == 0:
            # No parsing nor filtering for the root node
            return VisitResult(True, None, self.layouts)

        layouts_for_children: list[Layout] = []
        record = None
        for layout in self.layouts:
            # Prune non matching layouts for this directory. We need to test all
            # layouts to eliminate non matching layouts as early as possible in
            # a given branch
            result = layout.parse_node(dir_node.level - 1, dir_node.name)
            if result is not None:
                layouts_for_children.append(layout)
            if record is None:
                # Do not override a valid record with a None
                record = result

        if not layouts_for_children:
            # Outlier
            # If nobody matches, we do not want to explore further
            logger.debug(
                "Folder %s does not match any layout, branch exploration stopped.",
                dir_node.info["name"],
            )
            return VisitResult(False)

        if all(
            [
                not layout.test_record(dir_node.level - 1, record)
                for layout in layouts_for_children
            ]
        ):
            # This folder does not match the filtering criteria. It is ignored
            logger.debug(
                "Folder %s filtered out, branch exploration stopped",
                dir_node.info["name"],
            )
            return VisitResult(False)

        # Don't return a payload for dir nodes (will be subject to change later)
        return VisitResult(True, None, layouts_for_children)

    def visit_file(self, file_node: FileNode) -> VisitResult:
        """Visits a file node.

        The file node is interpreted to generate a record of structured
        information. The content of this record depends on the layouts
        definition. If the interpretation fails, the visit result will not
        include any information about the node.

        Layout filters are also applied to the node record. If all layouts
        exclude the node, the visit result will not include any information
        about the node.

        Returns
        -------
        :
            Node information and visit metadata. For file node, no further
            exploration should be needed. In this case, surviving layouts are
            not relevant and will not be included in the visit result.
        """
        logger.debug("Visiting file %s", file_node.info["name"])
        # Advance/prune layouts for files
        for layout in self.layouts:
            record = layout.parse_node(file_node.level - 1, file_node.name)
            if record is not None and layout.test_record(file_node.level - 1, record):
                # Files are leaf, no need to continue exploration
                return VisitResult(False, record)
        return VisitResult(False)

    def advance(self, result: VisitResult) -> LayoutVisitor:
        return LayoutVisitor(result.surviving_layouts)


def walk(node: INode, visitor: IVisitor) -> tp.Iterator[tp.Any]:
    """Recursive walk of a file system tree.

    This is a reimplementation of the similar :func:`os.walk` and
    :meth:`fsspec.spec.AbstractFileSystem.walk`. The motivation for the
    reimplementation is that we need to inject some complex logic (node parsing
    and branch exploration) during the tree traversal.

    Parameters
    ----------
    node
        File or folder node representing a path on the filesystem
    visitor
        Visitor that will process the note and produce some results

    Yields
    ------
    :
        The results of all visits in the tree. The result type will depend on
        the visitor implementation

    See Also
    --------
    StandardVisitor
        Visitor returning (root, dirs, files) tuples similar to a
        conventionnal walk
    LayoutVisitor
        Visitor that can interpret the node paths and return structured
        information
    """
    result = node.accept(visitor)
    if result.payload is not None:
        yield result.payload
    if not result.explore_next:
        return

    for child in node.children():
        yield from walk(child, visitor.advance(result))
