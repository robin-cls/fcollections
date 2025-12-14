from __future__ import annotations

import abc
import dataclasses as dc
import logging
import typing as tp

import fsspec

logger = logging.getLogger(__name__)

from fcollections.core import Layout


class INode(abc.ABC):

    def __init__(self, name: str, info: dict[str, tp.Any], level: int):
        self.name = name
        self.info = info
        self.level = level

    @abc.abstractmethod
    def accept(self, visitor: LayoutVisitor) -> VisitResult:
        pass

    @abc.abstractmethod
    def children(self) -> tp.Iterator[INode]:
        pass


class FileNode(INode):
    def accept(self, visitor: LayoutVisitor) -> VisitResult:
        return visitor.visit_file(self)

    def children(self) -> tp.Iterator[INode]:
        return []  # files have no children


class DirNode(INode):
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
    explore_next: bool
    payload: tp.Any | None = None
    surviving_layouts: list[Layout] | None = None


class IVisitor(abc.ABC):

    @abc.abstractmethod
    def visit_dir(self, dir_node: DirNode) -> VisitResult:
        pass

    @abc.abstractmethod
    def visit_file(self, file_node: DirNode) -> VisitResult:
        pass

    @abc.abstractmethod
    def advance(self, result: VisitResult) -> IVisitor:
        pass


class StandardVisitor(IVisitor):

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


def walk(node: INode, visitor: LayoutVisitor):
    result = node.accept(visitor)
    if result.payload is not None:
        yield result.payload
    if not result.explore_next:
        return

    for child in node.children():
        yield from walk(child, visitor.advance(result))
