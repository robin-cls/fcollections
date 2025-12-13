from __future__ import annotations

import abc
import logging
import os
import typing as tp
import warnings

import fsspec

from fcollections.time import (
    Period,
    fuse_successive_periods,
    periods_envelop,
    periods_holes,
    times_holes,
)

if tp.TYPE_CHECKING:  # pragma: no cover
    import numpy as np
    import pandas as pda_t

logger = logging.getLogger(__name__)


class ITemporalMixin(abc.ABC):

    @abc.abstractmethod
    def list_files(self, *args, **kwargs) -> pda_t.DataFrame:
        """The mixin relies on this method to build new functionalities."""

    @abc.abstractmethod
    def time_holes(self, **filters):
        """Find the holes in time coverage.

        Returns
        -------
        :
            A generator yielding Period representing holes in the data
        """

    @abc.abstractmethod
    def time_coverage(self, **filters) -> Period | None:
        """Find the time extent of the netcdf files.

        Returns
        -------
        :
            A Period representing the period covered by the data
        """


class PeriodMixin(ITemporalMixin):

    def time_holes(self, **filters) -> tp.Generator[Period, None, None]:
        periods = sorted(self.list_files(**filters)["time"].values)
        if len(periods) == 0:
            return []
        reduced = fuse_successive_periods(periods)
        return periods_holes(reduced)

    def time_coverage(self, **filters) -> Period | None:
        periods = sorted(self.list_files(**filters)["time"].values)
        if len(periods) == 0:
            return None
        return periods_envelop(periods)


class DiscreteTimesMixin(ITemporalMixin):

    def __init__(self, sampling: np.timedelta64 | None = None):
        self.sampling = sampling

    def time_holes(self, **filters) -> tp.Generator[Period, None, None]:
        if self.sampling is None:
            msg = """No sampling specified, holes detection in the time serie
            cannot proceed"""
            warnings.warn(msg)
            return []
        times = sorted(self.list_files(**filters)["time"].values)
        if len(times) == 0:
            return []
        return times_holes(times, self.sampling)

    def time_coverage(self, **filters) -> Period | None:
        times = sorted(self.list_files(**filters)["time"].values)
        if len(times) == 0:
            return None
        return Period(times[0], times[-1])


class DownloadMixin(abc.ABC):

    @property
    @abc.abstractmethod
    def fs(self) -> fsspec.AbstractFileSystem:
        """The mixin relies on this attribute to build new functionalities."""

    def download(self, files: list[str], local_path: str, force_download: bool = False):
        """Retrieve files from FTP to local path.

        Parameters
        ----------
        files: str
            list of file paths to copy locally
        local_path: str
            local path to copy files to
        force_download: boolean
            force download files (True) or don't download files if already exist locally (False)

        Returns
        -------
        the list of downloaded files
        """
        downloaded = []
        for file_path in files:
            local_file = os.path.join(local_path, os.path.basename(file_path))
            if force_download or not os.path.exists(local_file):
                try:
                    logger.info("Retrieving file: %s...", file_path)
                    self.fs.get_file(file_path, local_file)
                    downloaded.append(local_file)
                except TimeoutError as exc:
                    logger.exception("An error occured retrieving file %s", exc)

        return downloaded
