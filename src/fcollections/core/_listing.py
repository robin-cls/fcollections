from __future__ import annotations

import abc
import functools
import logging
import os
import typing as tp
import warnings
from pathlib import Path

import pandas as pda
from fsspec import AbstractFileSystem
from fsspec.implementations.local import LocalFileSystem

from ._codecs import DecodingError
from ._filenames import FileNameConvention, FileNameField

logger = logging.getLogger(__name__)


class FileListingError(Exception):
    """Raised when an error occurs during files discovery and
    interpretation."""


class ILayout:
    """Information about a multiple Tree levels.

    Given a Tree (ex a filesystem) with a structure of N homogeneous levels,
    the layout will associate each level with a FileNameConvention to extract
    useful information. This information can then be leveraged by building
    filters to speed up the tree visitation.

    For example, let's consider a set of altimetry data files, organized in
    pre-defined folders: v1/Expert/cycle_001, v1/Expert/cycle_002,
    v2/Basic/cycle_001, ...
    The first level contains information about the version, the second level
    about the subset, and the last level about the cycle number. The layout will
    declare three FileNameConvention to 'know' about the tree structure. Then,
    filters - for example subset='Expert' - can be set to select only a subpart
    of the tree, greatly improving the visitation performance.
    """

    @property
    @abc.abstractmethod
    def names(self) -> set[str]:
        """Names of the supported filters."""

    @abc.abstractmethod
    def generate(self, root: str, **fields: tp.Any) -> str:
        """Generate a path from the fields.

        Parameters
        ----------
        root
            The root path
        fields
            key/values for interpolating the conventions

        Returns
        -------
        :
            A path

        Raises
        ------
        ValueError
            In case one of the field required to generate the path is missing,
        ValueError
            In case one of the field required to generate the path has an
            improper value
        """

    @abc.abstractmethod
    def set_filters(self, **references: tp.Any):
        """Set filters used to check if a path complies with the layout.

        Parameters
        ----------
        **references
            Key/values matching at least one of the underlying conventions
        """

    @abc.abstractmethod
    def test(self, level: int, node: str) -> bool:
        """Checks if a path part matches the current filters.

        Parameters
        ----------
        node
            Path part that needs to be checked
        level
            Level of the current path part among the layout conventions

        Returns
        -------
        :
            True if the path part is selected with the current filters, False
            otherwise
        """


class Layout(ILayout):
    """Implements a ILayout with a succession of conventions.

    Parameters
    ----------
    conventions
        List of convention, with the first element matching the tree root, and
        last element the last level before the leafs

    See Also
    --------
    fcollections.core.FileNameConvention: the equivalent for the tree leafs (file
    names)
    """

    def __init__(self, conventions: list[FileNameConvention]):
        self.conventions = conventions
        self.set_filters()

    def generate(self, root: str, **fields: tp.Any) -> str:
        elements = []
        for convention in self.conventions:
            names = [f.name for f in convention.fields]
            element = convention.generate(
                **{k: v for k, v in fields.items() if k in names}
            )
            elements.append(element)

        return os.path.join(root, *elements)

    def set_filters(self, **references: tp.Any):
        filters = []
        unknown_references = set(references)
        for level, convention in enumerate(self.conventions):
            names = [f.name for f in convention.fields]

            filtered_references = {k: v for k, v in references.items() if k in names}
            unknown_references -= set(filtered_references)
            logger.debug(
                "Setting layout level %d filters to %s", level, filtered_references
            )
            filters.append(RecordFilter(convention.fields, **filtered_references))

        if len(unknown_references) > 0:
            msg = (
                "Layout has been configured with unknown references "
                f"'{unknown_references}'. They will be ignored."
            )
            warnings.warn(msg)

        self.filters: list[RecordFilter] = filters

    def test(self, level: int, node: str) -> bool:
        convention, record_filter = self.conventions[level], self.filters[level]
        try:
            record = convention.parse(convention.match(node))
        except (DecodingError, AttributeError):
            msg = (
                f"Actual node {node} did not match the expected convention "
                f"{convention.regex}. This is probably due to a mismatch "
                "between the layout and the actual tree structure"
            )
            warnings.warn(msg)
            return False
        return record_filter.test(record)

    @property
    def names(self) -> set[str]:
        return set(
            functools.reduce(
                lambda x, y: x + y,
                map(
                    lambda convention: [f.name for f in convention.fields],
                    self.conventions,
                ),
            )
        )


class CompositeLayout(ILayout):
    """Implements a heterogeneous layout.

    In case the folder structure is heterogeneous, we expect that some branches
    of the tree will show different paths. For example, exploring the L3_LR_SSH
    products gives:

      * ``<v3`` : [version]/[subset]/[cycle_number]
      * ``>=v3``: [version]/[subset]/[timeliness]/[cycle_number]

    This class solves the heterogeneity problem with a crude implementation,
    trying multiple layouts in succession until one of them matches/generates
    the tree path.

    For string generation, the first layout that works will be used to generate
    the path. Care must be taken when choosing the order of the layouts.

    See Also
    --------
    Layout: the implementation for a homogeneous folder structure
    """

    def __init__(self, layouts: list[Layout]):
        self._layouts = layouts

    def test(self, level: int, node: str) -> bool:
        bad = 0
        with warnings.catch_warnings(action="error"):
            # The default Layout implementation tries to detect a mismatch
            # between the configured layout and the actual tree. The Composite
            # layout tries to emulate the same behavior: a warning is emitted if
            # none of the layouts can parse the node (it is not filtered out, it
            # just does not match any of the regexes).
            # If the number of emitted warnings is the same as the layouts, it
            # means we are in a suspect case of bad layout
            for layout in self._layouts:
                try:
                    if layout.test(level, node):
                        return True
                except IndexError:
                    pass
                except UserWarning:
                    bad += 1

        if bad == len(self._layouts):
            msg = (
                f"Node {node} did not match any of the possible conventions."
                " This is probably due to a mismatch between the layouts and"
                " the actual tree structure"
            )
            warnings.warn(msg)
        return False

    def generate(self, root: str, **fields: abc.Any) -> str:
        for ii, layout in enumerate(self._layouts):
            try:
                path = layout.generate(root, **fields)
                logger.debug("Layout [%d] path generation success", ii)
                return path
            except ValueError:
                logger.debug("Layout [%d] path generation failed, trying next", ii)
        msg = "None of the configured layout could generate a path"
        raise ValueError(msg)

    def set_filters(self, **references: abc.Any):
        unknown_references = set(references)
        filtered_references = {k: v for k, v in references.items() if k in self.names}
        unknown_references -= set(filtered_references)

        with warnings.catch_warnings(action="ignore"):
            # Irrelevant filters will automatically be ignored by the underlying
            # layouts
            for layout in self._layouts:
                layout.set_filters(**filtered_references)

        if len(unknown_references) > 0:
            msg = (
                "Layout has been configured with unknown references "
                f"'{unknown_references}'. They will be ignored."
            )
            warnings.warn(msg)

    @property
    def names(self) -> set[str]:
        return functools.reduce(
            lambda a, b: a | b, [layout.names for layout in self._layouts]
        )


class ITreeIterable(abc.ABC):
    """List leafs in a tree-like structure.

    File systems are the most obvious case, with the leafs defined as
    files or links. Other tree-like structure may implement this
    interface, for example a remote server organizing URL in a tree
    structure.

    Some trees may have too many branches to search with respect to the actual
    need. The tree iterable can take a ILayout as a parameter to reduce the
    number of searched branches by applying a set of criteria (aka filters).
    This will prevent leafs from being generated improving generation speed and
    reducing the number of leafs to process for ITreeIterable callers

    Parameters
    ----------
    layout
        Layout allowing to guess the tree structure and eventually discard some
        branches along the search

    See Also
    --------
    Layout: inform about the tree structure and allows to apply filters to the
    search
    """

    def __init__(self, layout: Layout | None = None):
        self.layout = layout

    @abc.abstractmethod
    def find(
        self, root: str, detail: bool = False, **filters: tp.Any
    ) -> tp.Iterator[str | dict[str, str]]:
        """List all leafs below the given node.

        Parameters
        ----------
        root
            The tree node to start the search from
        detail
            Whether to return additionnal metadata for the leafs (defaults to
            False)
        **filters
            filters for node selection over the fields declared in the layout
            (optional). Each field can accept a different filter value depending
            on the underlying FileNameField subclass

        Yields
        ------
        :
            A string representing the path from root to a given leaf, or a
            dictionary if detail=True
        """


class FileSystemIterable(ITreeIterable):
    """List files or links in a file system.

    Parameters
    ----------
    fs
        The file system that needs to be iterated upon
    layout
        Layout allowing to guess the tree structure and eventually discard some
        branches along the search
    """

    def __init__(
        self,
        fs: AbstractFileSystem = LocalFileSystem(follow_symlinks=True),
        layout: Layout | None = None,
    ):
        super().__init__(layout)
        self.fs = fs

    def find(
        self, root: str, detail: bool = False, **filters: tp.Any
    ) -> tp.Iterator[str | dict[str, str]]:

        if len(filters) > 0 and self.layout is None:
            msg = (
                f"Filters {filters.keys()} have been defined for the file "
                "system tree walk, but no layout is configured. These "
                "filters will be ignored"
            )
            warnings.warn(msg)

        if self.layout is not None:
            self.layout.set_filters(**filters)

        for current, folders, files in self.fs.walk(root, topdown=True, detail=detail):
            if self.layout is not None:
                level = len(Path(current).relative_to(root).parts)

            for folder in tuple(folders):
                # Will also give the folder name if details=True (folders is a
                # dict with the folders names as keys)
                if self.layout is not None and not self.layout.test(level, folder):
                    logger.debug(
                        "Ignore folder %s", os.path.join(root, current, folder)
                    )
                    if not detail:
                        # Remove list element
                        folders.remove(folder)
                    else:
                        # Remove dictionary element. note how we iterate on a
                        # tuple copy of the folders keys
                        del folders[folder]
                else:
                    logger.debug(
                        "Search folder %s", os.path.join(root, current, folder)
                    )

            if detail:
                yield from files.values()
            else:
                yield from map(lambda f: os.path.join(root, current, f), files)


class RecordFilter:
    """Utility class for filtering values.

    Attributes
    ----------
    fields: List[FileNameField]
        the fields to filter
    **references:
        the values of fields used for selection
    """

    def __init__(self, fields: list[FileNameField], **references):
        self.fields = fields
        self.references = references

        fields_names = [f.name for f in fields]
        filter_keys = list(references.keys())

        # The FileNameParser will return a record that is ordered the same as
        # its fields. These fields are passed in the same order in this
        # RecordFilter, which is why we can assume that the fields and record
        # are in matching order here
        try:
            self.index_in_record = [fields_names.index(key) for key in filter_keys]
        except ValueError as exc:
            unknown_keys = set(filter_keys) - set(fields_names)
            raise FileListingError(
                f"Tried to build filter on file name fields using unknown keys: '{unknown_keys}'"
            ) from exc

        self._sanitize_references()

    def test(self, record):
        """Test if a record is filtered.

        Parameters
        ----------
        record:
            record to filter

        Returns
        -------
        boolean
            true if the record is filtered
        """
        return all(
            self.fields[index].test(reference, record[index])
            for reference, index in zip(self.references.values(), self.index_in_record)
        )

    def _sanitize_references(self):
        for (key, reference), index in zip(
            self.references.items(), self.index_in_record
        ):
            self.references[key] = self.fields[index].sanitize(reference)


class FileDiscoverer:
    """Utility class for discovering files in a file system.

    Attributes
    ----------
    parser: FileNameConvention
        filename convention allowing to parse the file names
    fs: AbstractFileSystem
        fsspec file system. Default: LocalFileSystem
    """

    def __init__(
        self, parser: FileNameConvention, iterable: ITreeIterable = FileSystemIterable()
    ):
        self.iterable = iterable
        self.convention = parser

    def list(
        self,
        path: str,
        predicates: tuple[tp.Callable[[tuple[tp.Any, ...]], bool], ...] = (),
        stat_fields: tuple[str] = (),
        **filters,
    ) -> pda.DataFrame:
        """List files in file system.

        Parameters
        ----------
        path: str
            path of directory containing files
        predicates
            Complex predicates run over the include/exclude a file from its
            associated record
        stat_fields
            Name of the file metadata fields that should be returned in the
            record. The info that can be retrieved is dependent on the file
            system implementation. Check the filesystem 'ls' method to get the
            available stat fields
        **filters
            filters for files/folders selection over the fields declared in the
            file name convention and layout (optional). Each field can accept a
            different filter value depending on the underlying FileNameField
            subclass

        Returns
        -------
        pda.DataFrame
            A pandas's dataframe containing all selected filenames + a column
            per field requested

        Raises
        ------
        KeyError
            In case some of the requested stat_fields are not available for the
            current file system
        """
        file_filters = {
            k: v
            for k, v in filters.items()
            if k in [f.name for f in self.convention.fields]
        }
        record_filter = RecordFilter(self.convention.fields, **file_filters)

        if self.iterable.layout is not None:
            layout_filters = {
                k: v for k, v in filters.items() if k in self.iterable.layout.names
            }
        else:
            layout_filters = {}

        # Build records
        if len(stat_fields) <= 0:
            records = (
                # Filter non matching filenames
                filter(
                    record_filter.test,
                    # Parse the result and append the filename to the record
                    map(
                        lambda file_match: (
                            *self.convention.parse(file_match[1]),
                            file_match[0],
                        ),
                        # Filter out non matching files
                        filter(
                            lambda file_match: file_match[1] is not None,
                            # Match file names
                            map(
                                lambda file: (
                                    file,
                                    self.convention.match(os.path.basename(file)),
                                ),
                                # Walk the folder and find the files
                                self.iterable.find(
                                    path, detail=False, **layout_filters
                                ),
                            ),
                        ),
                    ),
                )
            )
        else:
            records = (
                # Filter non matching filenames
                filter(
                    record_filter.test,
                    # Parse the result and append the filename and its requested
                    # metadata to the record
                    map(
                        lambda file_match_stats: (
                            *self.convention.parse(file_match_stats[1]),
                            file_match_stats[0],
                            *file_match_stats[2],
                        ),
                        # Filter out non matching files
                        filter(
                            lambda file_match_stats: file_match_stats[1] is not None,
                            # Match file names and filter the stats we want
                            map(
                                lambda file_stats: (
                                    file_stats["name"],
                                    self.convention.match(
                                        os.path.basename(file_stats["name"])
                                    ),
                                    tuple(file_stats[k] for k in stat_fields),
                                ),
                                # Walk the folder and find the files
                                self.iterable.find(path, detail=True, **layout_filters),
                            ),
                        ),
                    ),
                )
            )

        for predicate in predicates:
            records = filter(predicate, records)

        df = pda.DataFrame(
            records,
            columns=[f.name for f in self.convention.fields]
            + ["filename"]
            + list(stat_fields),
        )

        return df
