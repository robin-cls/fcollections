import re
from enum import Enum, auto

# This pattern is used for Swot data preprocessing
SWOT_PATTERN = re.compile(r"(.*)_(?P<cycle_number>\d{3})_(?P<pass_number>\d{3})_(.*)")


class Temporality(Enum):
    """Temporality of the L3_LR_SSH product.

    The L3_LR_SSH product is calibrated on nadir data. Nadir data has two
    temporalities in Copernicus Marine: reprocessed data (labelled as Multi-Year
    MY) and near-real time data (NRT).

    This temporality in upstream data is reflected as reproc/forward to
    adopt the SWOT mission denomination. It is **not** the same definition as
    the L2_LR_SSH, where reprocess data covers PGC, PGD, ... datasets and
    forward data covers PIC, PID, ...

    See Also
    --------
    Delay
        Copernicus Marine delay definition (in our case for Nadir data)
    fcollections.implementations.Timeliness
        L2_LR_SSH product temporality definition
    """

    #: Reprocessed data calibrated on the MY nadir dataset
    REPROC = auto()
    #: Forward data calibrated on the NRT nadir dataset
    FORWARD = auto()


class ProductSubset(Enum):
    """Swot product subset enum."""

    Basic = auto()
    Expert = auto()
    WindWave = auto()
    Unsmoothed = auto()
    Technical = auto()
    Light = auto()
    Extended = auto()
