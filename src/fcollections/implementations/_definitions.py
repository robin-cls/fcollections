from enum import Enum, auto


class Sensor(Enum):
    """Sensor enum."""
    OLCI = auto()
    MULTI = auto()


class ProductLevel(Enum):
    """Product level enum."""
    L1A = auto()
    L1B = auto()
    L2 = auto()
    L3 = auto()
    L4 = auto()


class Delay(Enum):
    NRT = auto()
    DT = auto()
    MY = auto()
    MYINT = auto()


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


class AcquisitionMode(Enum):
    IW = auto()
    EW = auto()
    WV = auto()
    SM = auto()


class S1AOWIProductType(Enum):
    SW = auto()
    GS = auto()


class S1AOWISlicePostProcessing(Enum):

    CC = auto()
    CM = auto()
    OCN = auto()


class OCVariable(Enum):

    PLANKTON = auto()
    REFLECTANCE = auto()
    TRANSP = auto()
    OPTICS = auto()
