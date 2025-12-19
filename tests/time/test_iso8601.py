import pytest

from fcollections.time import ISODuration, parse_iso8601_duration


@pytest.mark.parametrize(
    "input, expected",
    [
        ("PT15M", ISODuration(minutes=15)),
        ("P1D", ISODuration(days=1)),
        ("P1DT3H", ISODuration(days=1, hours=3)),
        ("P1W", ISODuration(weeks=1)),
    ],
)
def test_parse_iso8601_duration(input: str, expected: ISODuration):
    assert parse_iso8601_duration(input) == expected


def test_parse_error():
    with pytest.raises(ValueError):
        parse_iso8601_duration("P0.2W")


@pytest.mark.parametrize(
    "expected, input",
    [
        ("PT15M", ISODuration(minutes=15)),
        ("P1D", ISODuration(days=1)),
        ("P1DT3H", ISODuration(days=1, hours=3)),
        ("P1W", ISODuration(weeks=1)),
        ("P1Y4M2DT1H1S", ISODuration(years=1, months=4, days=2, hours=1, seconds=1)),
        ("PT0S", ISODuration()),
    ],
)
def test_to_string(input: ISODuration, expected: str):
    assert str(input) == expected
