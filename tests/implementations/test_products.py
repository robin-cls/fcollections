import numpy as np
import pytest
from numpy.testing import assert_array_equal

from fcollections.implementations import (
    L2Version,
    Timeliness,
    build_version_parser,
)


@pytest.fixture
def parser():
    return build_version_parser()


@pytest.mark.parametrize(
    "input, expected",
    [
        (b"None", L2Version()),
        (None, L2Version()),
        (b"Not a version", L2Version()),
        (b"PIC1_01", L2Version(Timeliness.I, "C", 1, 1)),
        (b"P?C?", L2Version(baseline="C")),
    ],
)
def test_from_bytes(input: bytes | None, expected: L2Version):
    actual = L2Version.from_bytes(input)
    assert actual == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        ("None", L2Version()),
        (None, L2Version()),
        ("Not a version", L2Version()),
        ("PIC1_01", L2Version(Timeliness.I, "C", 1, 1)),
        ("P?C?", L2Version(baseline="C")),
    ],
)
def test_from_string(input: bytes | None, expected: L2Version):
    actual = L2Version.from_string(input)
    assert actual == expected


def test_from_bytes_array():
    expected = [
        [L2Version(), L2Version(Timeliness.G, "B", 1, 2)],
        [L2Version(Timeliness.I, "A", 0, 1), L2Version(baseline="B")],
    ]

    inputs = [[None, b"PGB1_02"], [b"PIA0_01", b"P?B?"]]
    actual = L2Version.from_bytes_array(np.array(inputs))
    assert np.array_equal(actual, expected)


def test_from_string_array():
    expected = [
        [L2Version(), L2Version(Timeliness.G, "B", 1, 2)],
        [L2Version(Timeliness.I, "A", 0, 1), L2Version(baseline="B")],
    ]

    inputs = [[None, "PGB1_02"], ["PIA0_01", "P?B?"]]
    actual = L2Version.from_string_array(np.array(inputs))
    assert np.array_equal(actual, expected)


def test_not_equal():
    # Only comparison between objects is supported
    version = L2Version(Timeliness.I, "C", 1, 1)
    assert str(version) == "PIC1_01"
    assert version != str(version)


@pytest.mark.parametrize(
    "version, is_null",
    [
        (L2Version.from_string("None"), True),
        (L2Version.from_string("PIC0_03"), False),
    ],
)
def test_is_null(version, is_null):
    assert version.is_null == is_null


@pytest.mark.parametrize(
    "version, expected",
    [
        ("PIC0_01", (Timeliness.I, "C", 0, 1)),
        ("PGD1_42", (Timeliness.G, "D", 1, 42)),
    ],
)
def test_parser_nominal(parser, version, expected):
    actual = parser.parse(parser.match(version))
    assert actual == expected


@pytest.mark.parametrize("bad_version", ["PIC0_0", "PXC0_01", "AIC0_01", "PI11_01"])
def test_parser_error(parser, bad_version):
    with pytest.raises(AttributeError):
        parser.parse(parser.match(bad_version))


@pytest.mark.parametrize(
    "v1, v2, expected",
    [
        ("PGC0_01", "PIC2_01", (False, False, False, True, True)),
        ("PGC1_02", "PGC1_03", (False, True, True, False, False)),
        ("PIC2_01", "PIC1_03", (False, False, False, True, True)),
        ("PIB1_02", "PIC0_01", (False, True, True, False, False)),
        ("PIC0_01", "PIC0_01", (True, False, True, False, True)),
    ],
    ids=[
        "better_temporality",
        "lesser_product_counter",
        "higher_minor_version",
        "lesser_baseline",
        "equality",
    ],
)
def test_ordering(v1: str, v2: str, expected: tuple[bool, bool, bool, bool, bool]):
    v1 = L2Version.from_string(v1)
    v2 = L2Version.from_string(v2)

    assert expected == (v1 == v2, v1 < v2, v1 <= v2, v1 > v2, v1 >= v2)


@pytest.mark.parametrize(
    "input_array, cmp_operator, cmp_right_member, cmp_res",
    [
        ## TESTS to compare a np.array[L2Version] vs. a single L2Version
        (
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            "<",
            L2Version.from_string("PIC0_01"),
            np.array([[False, False, False, True], [False, False, False, True]]),
        ),
        (
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            "<=",
            L2Version.from_string("PIC0_01"),
            np.array([[True, False, False, True], [False, False, False, True]]),
        ),
        (
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            "==",
            L2Version.from_string("PIC0_01"),
            np.array([[True, False, False, False], [False, False, False, False]]),
        ),
        (
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            "!=",
            L2Version.from_string("PIC0_01"),
            np.array([[False, True, True, True], [True, True, True, True]]),
        ),
        (
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            ">=",
            L2Version.from_string("PIC0_01"),
            np.array([[True, False, True, False], [False, False, True, False]]),
        ),
        (
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            ">",
            L2Version.from_string("PIC0_01"),
            np.array([[False, False, True, False], [False, False, True, False]]),
        ),
        ## TESTS to compare a np.array[L2Version] vs. a single L2Version built from None
        (
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            "<",
            L2Version.from_string("None"),
            np.array([[False, False, False, False], [False, False, False, False]]),
        ),
        (
            # None is non-orderable so we return False for every orderable comparison with None, even '<=' / '>='
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            "<=",
            L2Version.from_string("None"),
            np.array([[False, False, False, False], [False, False, False, False]]),
        ),
        (
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            "==",
            L2Version.from_string("None"),
            np.array([[False, True, False, False], [True, True, False, False]]),
        ),
        (
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            "!=",
            L2Version.from_string("None"),
            np.array([[True, False, True, True], [False, False, True, True]]),
        ),
        (
            # None is non-orderable so we return False for every orderable comparison with None, even '<=' / '>='
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            ">=",
            L2Version.from_string("None"),
            np.array([[False, False, False, False], [False, False, False, False]]),
        ),
        (
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            ">",
            L2Version.from_string("None"),
            np.array([[False, False, False, False], [False, False, False, False]]),
        ),
        ## TESTS to compare two np.array[L2Version]
        (
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            "<",
            np.array(
                [
                    [L2Version.from_string("PIC0_01")] * 4,
                    [L2Version.from_string("PIC0_01")] * 4,
                ]
            ),
            np.array([[False, False, False, True], [False, False, False, True]]),
        ),
        (
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            "<=",
            np.array(
                [
                    [L2Version.from_string("PIC0_01")] * 4,
                    [L2Version.from_string("PIC0_01")] * 4,
                ]
            ),
            np.array([[True, False, False, True], [False, False, False, True]]),
        ),
        (
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            "==",
            np.array(
                [
                    [L2Version.from_string("PIC0_01")] * 4,
                    [L2Version.from_string("PIC0_01")] * 4,
                ]
            ),
            np.array([[True, False, False, False], [False, False, False, False]]),
        ),
        (
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            "!=",
            np.array(
                [
                    [L2Version.from_string("PIC0_01")] * 4,
                    [L2Version.from_string("PIC0_01")] * 4,
                ]
            ),
            np.array([[False, True, True, True], [True, True, True, True]]),
        ),
        (
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            ">=",
            np.array(
                [
                    [L2Version.from_string("PIC0_01")] * 4,
                    [L2Version.from_string("PIC0_01")] * 4,
                ]
            ),
            np.array([[True, False, True, False], [False, False, True, False]]),
        ),
        (
            np.array(
                [
                    ["PIC0_01", "None", "PIC0_02", "PIB1_01"],
                    [None, "None", "PID0_02", "PIB1_01"],
                ]
            ),
            ">",
            np.array(
                [
                    [L2Version.from_string("PIC0_01")] * 4,
                    [L2Version.from_string("PIC0_01")] * 4,
                ]
            ),
            np.array([[False, False, True, False], [False, False, True, False]]),
        ),
    ],
    ids=[
        "lt_single_val",
        "le_single_val",
        "eq_single_val",
        "not_eq_single_val",
        "ge_single_val",
        "gt_single_val",
        "lt_none",
        "le_none",
        "eq_none",
        "not_eq_none",
        "ge_none",
        "gt_none",
        "lt_array",
        "le_array",
        "eq_array",
        "not_eq_array",
        "ge_array",
        "gt_array",
    ],
)
def test_array_comparison(input_array, cmp_operator, cmp_right_member, cmp_res):
    """Tests L2Version comparison operators."""
    import operator

    ops_map = {
        "<": operator.lt,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
        ">=": operator.ge,
        ">": operator.gt,
    }

    versions = L2Version.from_string_array(input_array)

    assert_array_equal(ops_map[cmp_operator](versions, cmp_right_member), cmp_res)
