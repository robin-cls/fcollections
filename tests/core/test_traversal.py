import socket
import threading
from pathlib import Path

import pytest
from fsspec.implementations.ftp import FTPFileSystem
from fsspec.implementations.local import LocalFileSystem
from fsspec.implementations.memory import MemoryFileSystem
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

from fcollections.core._traversal import DirNode, StandardVisitor, walk


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
        (my_fc / filepath).parent.mkdir(parents=True)
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


def test_walk_layout():
    # nodes = list(walk(root_node, LayoutVisitor([Mock()])))
    pass
