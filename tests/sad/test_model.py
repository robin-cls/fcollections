import os
import shutil
from pathlib import Path

import pytest

import fcollections.sad as sad


class DummyFetcher(sad.IAuxiliaryDataFetcher):

    @property
    def keys(self) -> set[str]:
        return {"foo", "bar"}

    def _file_name(self, key: str) -> str:
        return f"myfile_{key}.txt"

    def _download(self, remote_file: str, target_folder: Path) -> Path:
        new_path = target_folder / remote_file
        new_path.touch()
        return new_path


def test_name():
    assert DummyFetcher().name == "dummy_fetcher"

    class CAPITALS(DummyFetcher):
        pass

    assert CAPITALS().name == "capitals"


@pytest.fixture
def env_variables(tmp_path):
    os.environ["SAD_DATA"] = (tmp_path / "sad").as_posix()
    os.environ["SAD_DATA_DUMMY_FETCHER"] = (tmp_path / "sad_alt").as_posix()

    yield tmp_path
    del os.environ["SAD_DATA"]
    del os.environ["SAD_DATA_DUMMY_FETCHER"]


@pytest.fixture
def expected_files(env_variables):
    sad_data_folder = env_variables / "sad"
    sad_data_alt_folder = env_variables / "sad_alt"
    user_folder = (Path("~") / ".config" / "sad").expanduser()

    files: list[Path] = []
    files.append(sad_data_alt_folder / "myfile_foo.txt")
    files.append(sad_data_folder / "dummy_fetcher" / "myfile_foo.txt")
    files.append(sad_data_folder / "myfile_foo.txt")
    files.append(user_folder / "myfile_foo.txt")

    for f in files:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.touch()

    yield files
    # sad_data_folder and sad_data_alt_folder are automatically cleaned with
    # pytest scope
    shutil.rmtree(user_folder)


@pytest.fixture(autouse=True)
def env_clean_user_sad(tmp_path):
    try:
        shutil.rmtree((Path("~") / ".config" / "sad").expanduser())
    except FileNotFoundError:
        pass
    return


def test_unknown_key():
    auxiliary_data = DummyFetcher()
    with pytest.raises(KeyError):
        auxiliary_data["baz"]


@pytest.fixture
def env_variables_empty_invalid(tmp_path):
    os.environ["SAD_DATA"] = ""
    os.environ["SAD_DATA_DUMMY_FETCHER"] = "i/dont/exist"
    yield tmp_path
    del os.environ["SAD_DATA"]
    del os.environ["SAD_DATA_DUMMY_FETCHER"]


def test_lookup_folders_empty(env_variables_empty_invalid):
    auxiliary_data = DummyFetcher()
    assert len(auxiliary_data.lookup_folders()) == 1


def test_file_priority(expected_files):
    """Given four available files, pick the one matching the priority set by
    default."""
    auxiliary_data = DummyFetcher()
    for expected_file in expected_files:
        # Remove the found file to check the next priority
        assert auxiliary_data["foo"] == expected_file
        assert expected_file.exists()
        expected_file.unlink()


def test_target_folder_default():
    """By default missing files are downloaded in the user home.

    Alternatively we can set a preferred target folder.
    """
    expected_file = (Path("~") / ".config" / "sad" / "myfile_foo.txt").expanduser()
    assert not expected_file.exists()
    auxiliary_data = DummyFetcher()
    assert auxiliary_data["foo"] == expected_file


def test_target_folder_override(tmp_path):
    expected_file = tmp_path / "myfile_foo.txt"
    assert not expected_file.exists()
    auxiliary_data = DummyFetcher(tmp_path)
    assert auxiliary_data["foo"] == expected_file
