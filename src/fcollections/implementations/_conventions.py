from __future__ import annotations

import re

import numpy as np

from fcollections.core import (
    FileNameConvention,
    FileNameFieldDateJulianDelta,
    FileNameFieldEnum,
    FileNameFieldString,
    Layout,
)
from fcollections.missions import MissionsPhases

# This pattern is used for Swot data preprocessing
SWOT_PATTERN = re.compile(r"(.*)_(?P<cycle_number>\d{3})_(?P<pass_number>\d{3})_(.*)")

INTERNAL_SLA_PATTERN = re.compile(r"msla_oer_merged_h_(?P<date>\d{5}).nc")

DESCRIPTIONS = {
    "cycle_number": (
        "Cycle number of the half orbit. A half orbit is "
        "identified using a cycle number and a pass number."
    ),
    "pass_number": (
        "Pass number of the half orbit. A half orbit is "
        "identified using a cycle number and a pass number."
    ),
    "time": "Period covered by the file.",
    "level": "Product level of the data.",
    "subset": (
        "Subset of the LR Karin products. The Basic, Expert and Technical subsets "
        "are defined on a reference grid, opening the possibility of stacking the "
        "files, whereas the Unsmoothed subset is defined on a different grid for "
        "each cycle. The Light and Extended subset are specific to the "
        "L3_LR_WIND_WAVE product."
    ),
    "production_date": (
        "Production date of a given file. The same granule is "
        "regenerated multiple times with updated corrections. Hence"
        " there can be multiple files for the same period, but with"
        " a different production date."
    ),
    "sensor": "Sensor.",
    "delay": "Delay.",
    "oc_variable": "Ocean color variable.",
    "temporal_resolution": "Temporal resolution, such as P1D, P1M.",
    "spatial_resolution": "Spatial resolution, such as 4km, 1km, 300M.",
    "version": (
        "Version of the L3_LR_WIND_WAVE and L3_LR_SSH Swot products (they share "
        'their versioning). This is a tri-number version x.y.z, where "x" denotes '
        'a major change in the product, "y" a minor change and "z" a fix.'
    ),
}


class FileNameConventionGriddedSLAInternal(FileNameConvention):

    def __init__(self):
        super().__init__(
            regex=INTERNAL_SLA_PATTERN,
            fields=[
                FileNameFieldDateJulianDelta(
                    "date",
                    reference=np.datetime64("1950-01-01T00"),
                    delta=np.timedelta64(1, "D"),
                    description=DESCRIPTIONS["time"],
                )
            ],
            generation_string="msla_oer_merged_h_{date!f}.nc",
        )


AVISO_L4_SWOT_LAYOUT = Layout(
    [
        FileNameConvention(
            re.compile(r"v(?P<version>.*)"),
            [FileNameFieldString("version")],
            "v{version!f}",
        ),
        FileNameConvention(
            re.compile(r"(?P<method>4dvarnet|4dvarqg|miost)"),
            [FileNameFieldString("method")],
            "{method}",
        ),
        FileNameConvention(
            re.compile(r"(?P<phase>.*)"),
            [FileNameFieldEnum("phase", MissionsPhases)],
            "{phase!f}",
        ),
    ]
)
