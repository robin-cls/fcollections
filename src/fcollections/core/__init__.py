"""Files collections.

This module brings together the classic operations done on a collection
of files (in other word a dataset stored in multiple files). This
operations are: layout (structure of the folders) minimal walk; file
name: parsing, filtering and interpretation; file reading: data loading,
combination and post-processing.
"""

from ._codecs import DecodingError, ICodec
from ._filenames import (
    CaseType,
    FileNameConvention,
    FileNameField,
    FileNameFieldDateDelta,
    FileNameFieldDateJulian,
    FileNameFieldDateJulianDelta,
    FileNameFieldDatetime,
    FileNameFieldEnum,
    FileNameFieldFloat,
    FileNameFieldInteger,
    FileNameFieldPeriod,
    FileNameFieldString,
)
from ._filesdb import (
    Deduplicator,
    FilesDatabase,
    IPredicate,
    NotExistingPathError,
    SubsetsUnmixer,
)
from ._listing import (
    DirNode,
    FileListingError,
    FileNode,
    FileSystemMetadataCollector,
    ILayout,
    INode,
    IVisitor,
    Layout,
    LayoutVisitor,
    NoLayoutVisitor,
    RecordFilter,
    StandardVisitor,
    VisitResult,
    walk,
)
from ._metadata import (
    GroupMetadata,
    VariableMetadata,
    group_metadata_from_netcdf,
)
from ._mixins import (
    DiscreteTimesMixin,
    DownloadMixin,
    ITemporalMixin,
    PeriodMixin,
)
from ._readers import IFilesReader, OpenMfDataset, compose
from ._testers import ITester

__all__ = [
    "FileNameField",
    "FileNameFieldDatetime",
    "FileNameFieldDateDelta",
    "FileNameFieldDateJulian",
    "FileNameFieldEnum",
    "FileNameFieldFloat",
    "FileNameFieldInteger",
    "FileNameFieldString",
    "FileNameFieldPeriod",
    "FileNameConvention",
    "FileListingError",
    "IFilesReader",
    "OpenMfDataset",
    "compose",
    "FilesDatabase",
    "SubsetsUnmixer",
    "Deduplicator",
    "RecordFilter",
    "NotExistingPathError",
    "FileNameFieldDateJulianDelta",
    "DownloadMixin",
    "CaseType",
    "PeriodMixin",
    "GroupMetadata",
    "group_metadata_from_netcdf",
    "VariableMetadata",
    "DiscreteTimesMixin",
    "ITemporalMixin",
    "IPredicate",
    "Layout",
    "DecodingError",
    "ICodec",
    "ITester",
    "ILayout",
    "INode",
    "FileNode",
    "DirNode",
    "IVisitor",
    "LayoutVisitor",
    "NoLayoutVisitor",
    "StandardVisitor",
    "walk",
    "VisitResult",
    "FileSystemMetadataCollector",
]
