from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture(scope='session', autouse=True)
def patch_test_geometries_path(resources_directory: Path):
    # Science geometries file contain half orbits number [532, 579]
    # Calval geometries file contain half orbits number [25, 26]
    test_path = resources_directory / 'KaRIn_2kms_[phase]_geometries_tests.geojson'
    with patch('fcollections.geometry._search.GEOMETRIES_PATH', str(test_path)):
        yield
