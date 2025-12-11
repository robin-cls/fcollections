import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def patch_test_geometries_path(resources_directory: Path):
    # Science geometries file contain half orbits number [532, 579]
    # Calval geometries file contain half orbits number [25, 26]

    # Overriding the SAD_DATA env var is sufficient to point the sad module
    # toward the test resources folder
    os.environ["SAD_DATA_KARIN_FOOTPRINTS"] = resources_directory.as_posix()
    yield
    del os.environ["SAD_DATA_KARIN_FOOTPRINTS"]
