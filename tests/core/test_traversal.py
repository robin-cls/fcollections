import re
import socket
import threading
import typing as tp
from enum import Enum, auto
from pathlib import Path

import numpy as np
import pytest
from fsspec.implementations.ftp import FTPFileSystem
from fsspec.implementations.local import LocalFileSystem
from fsspec.implementations.memory import MemoryFileSystem
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

from fcollections.core import (
    FileNameConvention,
    FileNameFieldDateDelta,
    FileNameFieldDatetime,
    FileNameFieldEnum,
    FileNameFieldFloat,
    FileNameFieldInteger,
    FileNameFieldPeriod,
    FileNameFieldString,
    Layout,
)
from fcollections.core._traversal import (
    DirNode,
    FileNode,
    LayoutVisitor,
    StandardVisitor,
    VisitResult,
    walk,
)
from fcollections.time import Period


@pytest.fixture(scope="session")
def filepaths() -> list[str]:
    # The files that we will use to test the listing and filtering using the
    # file names will allow us
    return [
        "root/RED/LR_000/file_000_.25_foo-bar_20230201_RED_20121101_20130705_20010101.txt",
        "root/BLUE/LR_001/file_001_.25_foo-bar_20230202_BLUE_20121101_20130705_20010101.txt",
        "root/GREEN/LR_002/file_002_.25_foo-bar_20230203_GREEN_20121101_20130705_20010101.txt",
        "root/RED/LR_003/file_003_1.75_foo-bar_20230204_RED_20121101_20130705_20010101.txt",
        "root/BLUE/LR_004/file_004_1.75_foo-bar_20230205_BLUE_20121101_20130705_20010101.txt",
        "root/GREEN/LR_005/file_005_1.75_foo-bar_20230206_GREEN_20121101_20130705_20010101.txt",
        "root/RED/HR_006/file_006_5.6_baz_20230207_RED_20221101_20230705_19500101.txt",
        "root/BLUE/HR_007/file_007_5.8_baz_20230208_BLUE_20221101_20230705_19500101.txt",
        "root/GREEN/HR_008/file_008_7.4_baz_20230209_GREEN_20221101_20230705_19500101.txt",
        "root/HR_009/file_009_5.6_baz_20230207_RED_20221101_20230705_19500101.txt",
        "root/HR_010/file_010_5.8_baz_20230208_BLUE_20221101_20230705_19500101.txt",
        "root/HR_011/file_011_7.4_baz_20230209_GREEN_20221101_20230705_19500101.txt",
        "root/RED/dead_branch",
        "root/HR_011/dead_branch",
        "root/dead_branch",
    ]


@pytest.fixture(scope="session")
def memory_fs() -> MemoryFileSystem:
    return MemoryFileSystem()


@pytest.fixture(scope="session")
def memory_root(memory_fs: MemoryFileSystem, filepaths: list[str]) -> Path:
    root = Path("/myfc")
    for filepath in filepaths:
        filepath = root / filepath
        memory_fs.makedirs(filepath.parent, exist_ok=True)
        memory_fs.touch(filepath)
    return root


@pytest.fixture(scope="session")
def ftp_server(tmp_path_factory: pytest.TempPathFactory):
    # Create a temp directory to act as FTP root
    ftp_root = tmp_path_factory.mktemp("myfc")

    # Setup user
    authorizer = DummyAuthorizer()
    authorizer.add_user(
        username="user",
        password="12345",
        homedir=str(ftp_root),
        perm="elradfmw",
    )

    handler = FTPHandler
    handler.authorizer = authorizer

    # Bind to random free port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        host, port = s.getsockname()

    server = FTPServer((host, port), handler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield {
        "host": host,
        "port": port,
        "username": "user",
        "password": "12345",
        "root": ftp_root,
    }

    server.close_all()


@pytest.fixture(scope="session")
def ftp_fs(ftp_server: list[str]) -> FTPFileSystem:
    fs = FTPFileSystem(
        host=ftp_server["host"],
        port=ftp_server["port"],
        username=ftp_server["username"],
        password=ftp_server["password"],
    )
    return fs


@pytest.fixture(scope="session")
def ftp_root(
    ftp_fs: FTPFileSystem, ftp_server: list[str], filepaths: list[str]
) -> FTPFileSystem:
    root = ftp_server["root"]
    for filepath in filepaths:
        filepath = root / filepath
        ftp_fs.makedirs(filepath.parent.as_posix(), exist_ok=True)
        ftp_fs.touch(filepath.as_posix())
    return root


@pytest.fixture
def local_fs() -> LocalFileSystem:
    return LocalFileSystem()


@pytest.fixture
def local_root(tmp_path_factory: pytest.TempPathFactory, filepaths: list[str]) -> Path:
    my_fc = tmp_path_factory.mktemp("myfc")
    for filepath in filepaths:
        (my_fc / filepath).parent.mkdir(parents=True, exist_ok=True)
        (my_fc / filepath).touch()
    return my_fc


class MockFS:

    def _strip_protocol(self, name: str):
        return name

    def ls(self, path, detail=True):
        # parent itself appears in its own listing
        return [
            {"name": f"{path}/", "type": "directory"},
            {"name": f"{path}/file1.txt", "type": "file"},
        ]


def test_walk_parent_pruning():
    mock_fs = MockFS()
    root_node = DirNode("root", {"name": "root"}, mock_fs, 0)

    nodes_reimpl = list(walk(root_node, StandardVisitor()))
    assert nodes_reimpl == [("root", [], ["", "file1.txt"])]


class MockErrorFS:

    def _strip_protocol(self, name: str):
        return name

    def ls(self, path, detail=True):
        raise FileNotFoundError


def test_walk_error():
    mock_fs = MockErrorFS()
    root_node = DirNode("root", {"name": "root"}, mock_fs, 0)

    nodes_reimpl = list(walk(root_node, StandardVisitor()))
    assert nodes_reimpl == [("root", [], [])]


@pytest.mark.parametrize(
    "fs_fixture_name, path_fixture_name",
    [
        ("local_fs", "local_root"),
        ("memory_fs", "memory_root"),
        ("ftp_fs", "ftp_root"),
    ],
    ids=["local", "memory", "ftp"],
)
def test_walk(
    fs_fixture_name: str, path_fixture_name: str, request: pytest.FixtureRequest
):
    fs = request.getfixturevalue(fs_fixture_name)
    root_path = request.getfixturevalue(path_fixture_name)
    root_str = root_path.as_posix()
    root_node = DirNode(root_str, {"name": root_str}, fs, 0)

    nodes_reimpl = list(walk(root_node, StandardVisitor()))
    nodes_fsspec = list(fs.walk(root_str))
    assert nodes_reimpl == nodes_fsspec


class Color(Enum):
    RED = auto()
    GREEN = auto()
    BLUE = auto()
    gray = auto()


@pytest.fixture(scope="session")
def layout(convention: FileNameConvention) -> Layout:
    return Layout(
        [
            FileNameConvention(
                re.compile(r"(?P<field_enum>\w+)"),
                [convention.get_field("field_enum")],
                "{field_enum!f}",
            ),
            FileNameConvention(
                re.compile(r"(?P<resolution>\w+)_(?P<field_i>\d{3})"),
                [FileNameFieldString("resolution"), FileNameFieldInteger("field_i")],
                "{resolution!f}_{field_i:>03d}",
            ),
        ]
    )


@pytest.fixture(scope="session")
def convention():
    regex = re.compile(
        r"file_(?P<field_i>\d+)_(?P<field_f>[+-]?([0-9]*[.])?[0-9]+)_(?P<field_s>[a-zA-Z0-9.-]+)_(?P<field_date>\d{8})_(?P<field_enum>\w+)_(?P<field_period>\d{8}_\d{8})_(?P<field_date_delta>\d{8}).txt"
    )
    fields = [
        FileNameFieldInteger("field_i"),
        FileNameFieldFloat("field_f"),
        FileNameFieldString("field_s"),
        FileNameFieldDatetime("field_date", "%Y%m%d"),
        FileNameFieldEnum("field_enum", Color),
        FileNameFieldPeriod("field_period", "%Y%m%d"),
        FileNameFieldDateDelta("field_date_delta", "%Y%m%d", np.timedelta64(1, "h")),
    ]
    generation_string = "file_{field_i:>03d}_{field_f}_{field_s}_{field_date!f}_{field_enum!f}_{field_period!f}_{field_date_delta!f}.txt"
    return FileNameConvention(regex, fields, generation_string)


@pytest.fixture(scope="session")
def layouts_v2(layout: Layout, convention: FileNameConvention) -> list[Layout]:
    return [
        Layout([*layout.conventions, convention]),
        Layout([layout.conventions[1], convention]),
    ]


@pytest.mark.parametrize(
    "path, level, expected_explore_next, layouts_selection",
    [
        ("root", 0, True, [0, 1]),
        ("root/RED", 1, True, [0]),
        ("root/HR_009", 1, True, [1]),
        ("root/outlier", 1, False, []),
    ],
)
def test_layout_visit_dir(
    layouts_v2: list[Layout],
    memory_fs: MemoryFileSystem,
    memory_root: Path,
    path: str,
    level: int,
    expected_explore_next: bool,
    layouts_selection: list[int],
):

    path = memory_root / path
    node = DirNode(path.name, {"name": path.as_posix()}, memory_fs, level)

    visitor = LayoutVisitor(layouts_v2)
    result = visitor.visit_dir(node)
    assert result.explore_next == expected_explore_next
    assert result.payload is None
    assert result.surviving_layouts == [layouts_v2[ii] for ii in layouts_selection]


@pytest.fixture(scope="session")
def expected_record() -> tuple[tp.Any, ...]:
    return (
        8,
        7.4,
        "baz",
        np.datetime64("2023-02-09T00:00:00.000000"),
        Color.GREEN,
        Period(np.datetime64("2022-11-01"), np.datetime64("2023-07-05")),
        Period(
            np.datetime64("1950-01-01"),
            np.datetime64("1950-01-01T01"),
            include_stop=False,
        ),
    )


@pytest.mark.parametrize(
    "path, level, layouts_selection",
    [
        (
            "root/GREEN/HR_008/file_008_7.4_baz_20230209_GREEN_20221101_20230705_19500101.txt",
            3,
            [0],
        ),
        (
            "root/HR_009/file_008_7.4_baz_20230209_GREEN_20221101_20230705_19500101.txt",
            2,
            [1],
        ),
    ],
)
def test_layout_visit_file(
    layouts_v2: list[Layout],
    memory_fs: MemoryFileSystem,
    memory_root: Path,
    path: str,
    level: int,
    expected_record: tuple[tp.Any, ...],
    layouts_selection: list[int],
):
    path = memory_root / path
    node = FileNode(path.name, {"name": path.as_posix()}, level)

    # Simulate layout pruning
    visitor = LayoutVisitor([layouts_v2[ii] for ii in layouts_selection])

    result = visitor.visit_file(node)
    assert not result.explore_next
    assert result.surviving_layouts == []

    assert result.payload == expected_record


def test_layout_advance(layouts_v2: list[Layout]):
    visitor = LayoutVisitor(layouts_v2)
    result = VisitResult(True, None, layouts_v2)
    new_visitor = visitor.advance(result)
    assert new_visitor is not visitor

    result = VisitResult(True, None, layouts_v2[:1])
    new_visitor = visitor.advance(result)
    assert len(new_visitor.layouts) == 1
    assert len(visitor.layouts) == 2

    # FileNameFieldInteger("field_i"),
    # FileNameFieldFloat("field_f"),
    # FileNameFieldString("field_s"),
    # FileNameFieldDatetime("field_date", "%Y%m%d"),
    # FileNameFieldEnum("field_enum", Color),
    # FileNameFieldPeriod("field_period", "%Y%m%d"),
    # FileNameFieldDateDelta("field_date_delta", "%Y%m%d", np.timedelta64(1, "h")),

    # "root/BLUE/LR_001/file_001_.25_foo-bar_20230202_BLUE_20121101_20130705_20010101.txt",
    # "root/GREEN/LR_002/file_002_.25_foo-bar_20230203_GREEN_20121101_20130705_20010101.txt",
    # "root/RED/LR_003/file_003_1.75_foo-bar_20230204_RED_20121101_20130705_20010101.txt",
    # "root/BLUE/LR_004/file_004_1.75_foo-bar_20230205_BLUE_20121101_20130705_20010101.txt",
    # "root/GREEN/LR_005/file_005_1.75_foo-bar_20230206_GREEN_20121101_20130705_20010101.txt",
    # "root/RED/HR_006/file_006_5.6_baz_20230207_RED_20221101_20230705_19500101.txt",
    # "root/BLUE/HR_007/file_007_5.8_baz_20230208_BLUE_20221101_20230705_19500101.txt",
    # "root/GREEN/HR_008/file_008_7.4_baz_20230209_GREEN_20221101_20230705_19500101.txt",
    # "root/HR_009/file_009_5.6_baz_20230207_RED_20221101_20230705_19500101.txt",
    # "root/HR_010/file_010_5.8_baz_20230208_BLUE_20221101_20230705_19500101.txt",
    # "root/HR_011/file_011_7.4_baz_20230209_GREEN_20221101_20230705_19500101.txt",


@pytest.mark.parametrize(
    "filters, record_index, expected, count",
    [({"field_enum": "BLUE"}, 4, Color.BLUE, 4), ({"field_f": "5.6"}, 1, 5.6, 2)],
)
def test_walk_layout(
    layouts_v2: list[Layout],
    filters: dict[str, tp.Any],
    record_index: int,
    expected: tp.Any,
    count: int,
    memory_root: Path,
    memory_fs: MemoryFileSystem,
):
    for layout in layouts_v2:
        layout.set_filters(**filters)
    visitor = LayoutVisitor(layouts_v2)
    root_str = (memory_root / "root").as_posix()
    root_node = DirNode(root_str, {"name": root_str}, memory_fs, 0)

    records = list(walk(root_node, visitor))
    assert len(records) == count
    assert all([record[record_index] == expected for record in records])
