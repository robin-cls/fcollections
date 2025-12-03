import abc
import datetime as dt
import re
import typing as tp
from enum import Enum, auto

import numpy as np

from fcollections.time import (
    Period,
    fractional_julian_day_to_numpy,
    julian_day_to_numpy,
    numpy_to_fractional_julian_day,
    numpy_to_julian_day,
)

T = tp.TypeVar("T")


class ICodec(abc.ABC, tp.Generic[T]):
    """Coder-Decoder interface.

    A codec defines how to encode/decode strings to/from a given T class
    object.
    """

    @abc.abstractmethod
    def decode(self, input_string: str) -> T:
        """Decode an input string and generate a Generic[T] object.

        Parameters
        ----------
        input_string
            The input string

        Returns
        -------
        :
            The decoded Generic[T] object

        Raises
        ------
        DecodingError
            If the input string decoding fails
        """

    @abc.abstractmethod
    def encode(self, data: T) -> str:
        """Encode a Generic[T] object into a string.

        Parameters
        ----------
        data
            The input Generic[T] object

        Returns
        -------
        :
            The encoded string
        """


class StringCodec(ICodec[str]):
    """Coder-Decoder implementation for string."""

    def decode(self, input_string: str) -> str:
        return input_string

    def encode(self, data: str) -> str:
        return data


class IntegerCodec(ICodec[int]):
    """Coder-Decoder implementation for integer numbers."""

    def decode(self, input_string: str) -> int:
        try:
            output_integer = int(input_string)
        except ValueError as exc:
            # In case the integer conversion failed. This should not happen if
            # the input regex is properly configured (with groups defined with
            # \d)
            msg = f"'{input_string}' could not be converted to a integer."
            raise DecodingError(msg) from exc

        return output_integer

    def encode(self, data: int) -> str:
        return str(data)


class FloatCodec(ICodec[float]):
    """Coder-Decoder implementation for float numbers."""

    def decode(self, input_string: str) -> float:
        try:
            output_float = float(input_string)
        except ValueError as exc:
            # In case the float conversion failed. This should not happen if
            # the input regex is properly configured (with groups defined with
            # \d)
            msg = f"'{input_string}' could not be converted to a float."
            raise DecodingError(msg) from exc

        return output_float

    def encode(self, data: float) -> str:
        return str(data)


class CaseType(Enum):
    upper = auto()
    lower = auto()


class EnumCodec(ICodec[type[Enum]]):
    """Coder-Decoder implementation for enumerations.

    The enumeration decoding and encoding can be c

    Parameters
    ----------
    enum_cls
        Enumeration class
    case_type_decoded
        Case transformation applied to the string before trying to decode it.
        Set to None if the string to decode is expected to have the same case as
        the enumeration label.
    case_type_encoded
        Case transformation applied to the enumeration label. Set to None to
        keep the enumeration label case.
    """

    def __init__(
        self,
        enum_cls: type[Enum],
        case_type_decoded: CaseType | None = None,
        case_type_encoded: CaseType | None = None,
    ):
        self.enum_cls = enum_cls
        if isinstance(case_type_decoded, str):
            case_type_decoded = CaseType[case_type_decoded]
        self.case_type_decoded = case_type_decoded

        if isinstance(case_type_encoded, str):
            case_type_encoded = CaseType[case_type_encoded]
        self.case_type_encoded = case_type_encoded

    def decode(self, input_string: str) -> type[Enum]:
        # Handle difference cases
        if self.case_type_decoded == CaseType.upper:
            input_string = input_string.upper()
        elif self.case_type_decoded == CaseType.lower:
            input_string = input_string.lower()

        try:
            output_enum = self.enum_cls[input_string]
        except KeyError as exc:
            msg = (
                f"'{input_string}' could not be converted to a "
                f"{self.enum_cls.__name__} enum."
            )
            raise DecodingError(msg) from exc

        return output_enum

    def encode(self, data: type[Enum]) -> str:
        if self.case_type_encoded == CaseType.upper:
            return data.name.upper()
        elif self.case_type_encoded == CaseType.lower:
            return data.name.lower()
        else:
            return data.name


class DateTimeCodec(ICodec[np.datetime64]):
    """Coder-Decoder implementation for datetimes."""

    def __init__(self, date_fmt: str | list[str]):
        if isinstance(date_fmt, str):
            date_fmt = [date_fmt]
        self.date_fmt = date_fmt

    def decode(self, input_string: str) -> np.datetime64:
        output_date = None
        for d_fmt in self.date_fmt:
            try:
                output_date = np.datetime64(dt.datetime.strptime(input_string, d_fmt))
                break
            except ValueError:
                continue

        if not output_date:
            # In case the date conversion failed. This should not happen if
            # the input regex is properly configured (with groups defined with
            # \d)
            msg = (
                f"'{input_string}' could not be converted to a numpy "
                f"datetime using formats {self.date_fmt}."
            )
            raise DecodingError(msg)

        return output_date

    def encode(self, data: np.datetime64) -> str:
        # dt.datetime does not handle nanosecond precision, so we must convert
        # the numpy timestamp before using dt.datetime to encode the date with
        # the given format
        return data.astype("M8[us]").astype(dt.datetime).strftime(self.date_fmt[0])


class PeriodDeltaCodec(ICodec[Period]):
    """Coder-Decoder implementation for periods.

    This implementation defines periods with the start date and a time delta

    Note
    ----

    This class complements time codecs. It relies on their time decoding and
    encoding capabilities to build the periods. PeriodDeltaCodec should be
    declared after the time codec in the class hierachy so that the super()
    calls works properly

    Parameters
    ----------
    delta
        Delta to deduce the end date of the period from its start date
    include_stop
        Whether the end date of the period is included

    See Also
    --------
    PeriodCodec: implementation with periods defined by a start date and end
    date
    DateTimeCodec: codec for datetime, can be used as a base for this mixin
    JulianDayCodec: codec for julian days, can be used as a base for this mixin
    """

    def __init__(self, delta: np.timedelta64, include_stop: bool = False):
        self.delta = delta
        self.include_stop = include_stop

    def decode(self, input_string: str) -> Period:
        output_date = super().decode(input_string)
        return Period(
            output_date, output_date + self.delta, include_stop=self.include_stop
        )

    def encode(self, data: Period) -> str:
        return super().encode(data.start)


class PeriodCodec(ICodec[Period]):
    """Coder-Decoder implementation for periods.

    This implementation defines periods with a start date and an end date

    Parameters
    ----------
    date_fmt
        Date format for parsing a string date
    separator
        Separator of two dates in the string to decode

    See Also
    --------
    PeriodDeltaCodec: implementation with periods defined by a start date and a
    time delta
    """

    def __init__(
        self,
        date_fmt: str,
        separator="_",
    ):
        self.date_fmt = date_fmt
        self.separator = separator

    def decode(self, input_string: str) -> Period:
        # If the separator is present in the date format
        if self.separator in self.date_fmt:
            # Find the middle separator and split to get the begin/end dates
            positions = [
                match.start() for match in re.finditer(self.separator, input_string)
            ]
            po = positions[len(positions) // 2]
            split = [input_string[:po], input_string[po + 1 :]]
        else:
            # Split the period in 2 to get the begin/end dates
            split = input_string.split(self.separator)

        if len(split) != 2:
            msg = (
                f"'{input_string} could not be converted to a Period because"
                " it could not be separated in two begin/end dates using "
                f"separator '{self.separator}'"
            )
            raise DecodingError(msg)

        try:
            start_date = np.datetime64(dt.datetime.strptime(split[0], self.date_fmt))
            end_date = np.datetime64(dt.datetime.strptime(split[1], self.date_fmt))
        except ValueError as exc:
            # In case the date conversion failed. This should not happen if
            # the input regex is properly configured (with groups defined with
            # \d)
            msg = (
                f"'{input_string}' could not be converted to a Period "
                "because one of its dates could not be converted to a "
                "datetime"
            )
            raise DecodingError(msg) from exc

        return Period(start_date, end_date)

    def encode(self, data: Period) -> str:
        # dt.datetime does not handle nanosecond precision, so we must convert
        # the numpy timestamp before using dt.datetime to encode the date with
        # the given format
        start = data.start.astype("M8[us]").astype(dt.datetime).strftime(self.date_fmt)
        stop = data.stop.astype("M8[us]").astype(dt.datetime).strftime(self.date_fmt)
        return start + self.separator + stop


class JulianDayCodec(ICodec[np.datetime64]):
    """Coder-Decoder implementation for datetimes given as julian days.

    Parameters
    ----------
    julian_days_format
        Whether the julian days will be given as 10583, 10573_10 or 10573.05
    reference
        The reference for the julian days

    Raises
    ------
    ValueError
        If the input julian_day_format does not match any expected format
    """

    FORMATS = ["days", "days_hours", "fractional"]

    def __init__(self, julian_day_format: str, reference: np.datetime64):
        if julian_day_format not in self.FORMATS:
            msg = f"Unknown julian day format {julian_day_format}, acceptable options are {self.FORMATS}"
            raise ValueError(msg)
        self.format = julian_day_format
        self.reference = reference

    def decode(self, input_string: str) -> np.datetime64:
        try:
            if self.format == "days_hours":
                split = input_string.split("_")
                output_date = julian_day_to_numpy(
                    (int(split[0]), int(split[1]), 0), reference=self.reference
                )
            elif self.format == "days":
                output_date = julian_day_to_numpy(
                    (int(input_string), 0, 0), reference=self.reference
                )
            else:
                output_date = fractional_julian_day_to_numpy(
                    float(input_string), reference=self.reference
                )
            return output_date
        except (ValueError, IndexError) as e:
            raise DecodingError(
                f'{input_string} is not a julian day matching format "{self.format}"'
            ) from e

    def encode(self, data: np.datetime64) -> str:
        # Convert the start. Much like the decoding, the delta is a given
        # variable and should not be part of the encoded string
        if self.format == "days_hours":
            days, hours, _ = numpy_to_julian_day(data, reference=self.reference)
            return f"{days:0>5d}_{hours:0>2d}"
        elif self.format == "days":
            days, _, _ = numpy_to_julian_day(data, reference=self.reference)
            return f"{days:0>2d}"
        else:
            fractional_days = numpy_to_fractional_julian_day(
                data, reference=self.reference
            )
            return str(fractional_days)


class DecodingError(Exception):
    """Raised by a codec if a string cannot be properly decoded."""
