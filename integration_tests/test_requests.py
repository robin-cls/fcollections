import shutil
from pathlib import Path

import pytest

from fcollections.sad import GSHHG, KarinFootprints


@pytest.fixture
def clean_user_config():
    try:
        original = (Path("~") / ".config" / "sad").expanduser()
        backup = (Path("~") / ".config" / "sad.backup").expanduser()
        shutil.move(original, backup)
        yield
        shutil.rmtree(original)
        shutil.move(backup, original)
    except FileNotFoundError:
        yield


@pytest.fixture
def karin_footprints(tmp_path):
    return KarinFootprints(tmp_path)


@pytest.fixture
def gshhg(tmp_path):
    return GSHHG(tmp_path)


@pytest.mark.parametrize("source_name", ["karin_footprints", "gshhg"])
def test_real_download(tmpdir, source_name, clean_user_config, request):
    source = request.getfixturevalue(source_name)

    assert len(list(source.preferred_target_folder.iterdir())) == 0
    for key in source.keys:
        source[key]
    # There can be uncompressed files in addition the ones specified by a given
    # key
    assert len(list(source.preferred_target_folder.iterdir())) >= len(source.keys)
