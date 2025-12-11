import shutil
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from fcollections.sad import GSHHG, KarinFootprints, app

runner = CliRunner()


@pytest.fixture
def clean_user_config():
    try:
        original = (Path("~") / ".config" / "sad").expanduser()
        backup = (Path("~") / ".config" / "sad.backup").expanduser()
        shutil.move(original, backup)
        yield
        shutil.rmtree(original)
        shutil.move(backup, original)
    except (FileNotFoundError, shutil.Error):
        yield


@pytest.fixture
def clean_env():
    return {
        "SAD_DATA": None,
        "SAD_DATA_KARIN_FOOTPRINTS": None,
        "SAD_DATA_GSHHG": None,
        # Set a large width for the terminal to avoid overflow handling by rich
        "COLUMNS": "120",
    }


def test_summary(clean_user_config, clean_env):
    result = runner.invoke(app, ["summary"], env=clean_env)

    expected_lines = [
        ["Type", "Available", "Keys", "Lookup Folders"],
        ["gshhg", "0/15", "GSHHS_c,GSHHS_f,GSHHS_h", ".config/sad"],
        ["karin_footprints", "0/2", "calval,science", ".config/sad"],
    ]

    assert result.exit_code == 0
    for line in expected_lines:
        for element in line:
            assert element in result.stdout


def test_details(clean_user_config, clean_env):
    result = runner.invoke(app, ["details", "karin_footprints"], env=clean_env)

    expected_lines = [
        ["Keys", "File Name", "Folder", "Present"],
        ["calval", "KaRIn_2kms_calval_geometries.geojson.zip", ".config/sad", "False"],
        [
            "science",
            "KaRIn_2kms_science_geometries.geojson.zip",
            ".config/sad",
            "False",
        ],
    ]

    assert result.exit_code == 0
    for line in expected_lines:
        for element in line:
            assert element in result.stdout


def test_env(tmp_path):
    expected_lines = [
        ["SAD_DATA", "UNSET"],
        ["SAD_DATA_GSHHG", tmp_path.as_posix()],
        ["SAD_DATA_KARIN_FOOTPRINTS", "INVALID"],
    ]

    result = runner.invoke(
        app,
        ["env"],
        env={
            "SAD_DATA": None,
            "SAD_DATA_KARIN_FOOTPRINTS": tmp_path.as_posix(),
            "SAD_DATA_GSHHG": "",
            "COLUMNS": "120",
        },
    )

    assert result.exit_code == 0
    for line in expected_lines:
        for element in line:
            assert element in result.stdout


@pytest.fixture
def download_env(tmp_path):
    return {
        "SAD_DATA": tmp_path.as_posix(),
        "SAD_DATA_KARIN_FOOTPRINTS": None,
        "SAD_DATA_GSHHG": None,
        # Set a large width for the terminal to avoid overflow handling by rich
        "COLUMNS": "120",
    }


def test_download(download_env):
    result = runner.invoke(app, ["summary"], env=download_env)
    assert result.exit_code == 0
    assert "0/15" in result.stdout
    assert "0/2" in result.stdout

    # Custom behavior for the mock
    def fake_download(remote_file: str, target_folder: Path) -> Path:
        file_path = target_folder / remote_file
        file_path.touch()
        return file_path

    with ExitStack() as stack:
        for cls in [GSHHG, KarinFootprints]:
            stack.enter_context(
                patch.object(cls, "_download", side_effect=fake_download)
            )
        result = runner.invoke(
            app, ["download", download_env["SAD_DATA"]], env=download_env
        )

    assert result.exit_code == 0

    result = runner.invoke(app, ["summary"], env=download_env)
    assert result.exit_code == 0
    assert "15/15" in result.stdout
    assert "2/2" in result.stdout
