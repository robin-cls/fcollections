from __future__ import annotations

import logging
import typing as tp

import requests

from ._interface import IAuxiliaryDataFetcher

if tp.TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class KarinFootprints(IAuxiliaryDataFetcher):
    """Karin geometries footprints.

    Each mission phase has its own orbit thus its own footprint. Available keys
    are the lower case mission phases: 'calval' and 'science'

    Parameters
    ----------
    preferred_target_folder
        The folder where data will be downloaded if it is missing. Default to
        the user home (~/.config/sad)
    """

    HTTP_URL = 'https://www.aviso.altimetry.fr/fileadmin/documents/missions/Swot'

    @property
    def keys(self) -> set[str]:
        return {'calval', 'science'}

    def _download(self, remote_file: str, target_folder: Path):
        fetch_http_file(self.HTTP_URL, remote_file, target_folder)
        return target_folder / remote_file

    def _file_name(self, key: str) -> str:
        # TODO: placeholder for the real thing
        if key == 'calval':
            return 'sph_calval_swath.zip'
        else:
            return 'swot_science_orbit_sept2015-v2_10s_swath.zip'
        #return f'KaRIn_2kms_{key}_geometries.nc'


def fetch_http_file(url: str, filename: str, target_folder: Path):

    full_url = url + '/' + filename

    logger.info('Downloading %s...', full_url)
    response = requests.get(full_url, timeout=60)
    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f'Failed to download file from {full_url}') from e

    with open(target_folder / filename, 'wb') as f:
        f.write(response.content)
    logger.info('Downloading %s... Done', full_url)
