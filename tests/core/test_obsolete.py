from __future__ import annotations

import re
import typing as tp
from enum import Enum, auto
from pathlib import Path

import numpy as np
import pytest
from fsspec.implementations.memory import MemoryFileSystem

from fcollections.core import (
    CompositeLayout,
    FileDiscoverer,
    FileNameConvention,
    FileNameFieldDateDelta,
    FileNameFieldDatetime,
    FileNameFieldEnum,
    FileNameFieldFloat,
    FileNameFieldInteger,
    FileNameFieldPeriod,
    FileNameFieldString,
    FileSystemIterable,
    Layout,
)
from fcollections.time import Period


class Size(Enum):
    S = auto()
    M = auto()
    L = auto()


class Color(Enum):
    RED = auto()
    GREEN = auto()
    BLUE = auto()
    gray = auto()


@pytest.fixture(scope="session")
def filepaths() -> list[str]:
    # The files that we will use to test the listing and filtering using the
    # file names will allow us
    return [
        "root/RED/LR_000/file_000_.25_foo-bar_20230201_RED_20121101_20130705_20010101.txt",
        "root/BLUE/LR_001/file_001_.25_foo-bar_20230202_BLUE_20121101_20130705_20010101.txt",
        "root/GREEN/LR_002/file_002_.25_foo-bar_20230203_GREEN_20121101_20130705_20010101.txt",
        "root/RED/LR_003/file_003_1.75_foo-bar_20230204_RED_20121101_20130705_20010101.txt",
        "root/BLUE/LR_004/file_004_1.75_foo-bar_20230205_BLUE_20121101_20130705_20010101.txt",
        "root/GREEN/LR_005/file_005_1.75_foo-bar_20230206_GREEN_20121101_20130705_20010101.txt",
        "root/RED/HR_006/file_006_5.6_baz_20230207_RED_20221101_20230705_19500101.txt",
        "root/BLUE/HR_007/file_007_5.8_baz_20230208_BLUE_20221101_20230705_19500101.txt",
        "root/GREEN/HR_008/file_008_7.4_baz_20230209_GREEN_20221101_20230705_19500101.txt",
    ]


@pytest.fixture(scope="session")
def convention():
    regex = re.compile(
        r"file_(?P<field_i>\d+)_(?P<field_f>[+-]?([0-9]*[.])?[0-9]+)_(?P<field_s>[a-zA-Z0-9.-]+)_(?P<field_date>\d{8})_(?P<field_enum>\w+)_(?P<field_period>\d{8}_\d{8})_(?P<field_date_delta>\d{8}).txt"
    )
    fields = [
        FileNameFieldInteger("field_i"),
        FileNameFieldFloat("field_f"),
        FileNameFieldString("field_s"),
        FileNameFieldDatetime("field_date", "%Y%m%d"),
        FileNameFieldEnum("field_enum", Color),
        FileNameFieldPeriod("field_period", "%Y%m%d"),
        FileNameFieldDateDelta("field_date_delta", "%Y%m%d", np.timedelta64(1, "h")),
    ]
    generation_string = "file_{field_i:>03d}_{field_f}_{field_s}_{field_date!f}_{field_enum!f}_{field_period!f}_{field_date_delta!f}.txt"
    return FileNameConvention(regex, fields, generation_string)


@pytest.fixture(scope="session")
def layout(convention: FileNameConvention) -> Layout:
    return Layout(
        [
            FileNameConvention(
                re.compile(r"(?P<field_enum>\w+)"),
                [convention.get_field("field_enum")],
                "{field_enum!f}",
            ),
            FileNameConvention(
                re.compile(r"(?P<resolution>\w+)_(?P<field_i>\d{3})"),
                [FileNameFieldString("resolution"), FileNameFieldInteger("field_i")],
                "{resolution!f}_{field_i:>03d}",
            ),
        ]
    )


@pytest.fixture(scope="session")
def composite_layout(convention: FileNameConvention, layout: Layout) -> CompositeLayout:
    layout_2 = Layout(
        [
            layout.conventions[0],
            FileNameConvention(
                re.compile(r"(?P<field_size>S|M|L)"),
                [FileNameFieldEnum("field_size", Size)],
                "{field_size!f}",
            ),
            layout.conventions[1],
        ]
    )
    return CompositeLayout([layout_2, layout])


def test_composite_layout_names(composite_layout: CompositeLayout):
    assert composite_layout.names == {
        "field_enum",
        "field_i",
        "resolution",
        "field_size",
    }


def test_composite_layout_generate_0(composite_layout: CompositeLayout):
    actual = composite_layout.generate(
        "root", field_enum=Color.RED, field_i=12, resolution="HR"
    )
    expected = "root/RED/HR_012"
    assert actual == expected


def test_composite_layout_generate_1(composite_layout: CompositeLayout):
    actual = composite_layout.generate(
        "root", field_enum=Color.RED, field_i=12, resolution="HR", field_size=Size.S
    )
    expected = "root/RED/S/HR_012"
    assert actual == expected


def test_composite_layout_generate_missing_field(composite_layout: Layout):
    with pytest.raises(ValueError):
        composite_layout.generate("root", field_i=12, resolution="HR")


def test_composite_layout_generate_bad_field(composite_layout: CompositeLayout):
    with pytest.raises(ValueError):
        composite_layout.generate(
            "root", field_enum=Color.RED, field_i="12", resolution="HR"
        )


@pytest.mark.parametrize(
    "filters, level, node, expected",
    [
        ({}, 0, "BLUE", True),
        ({"field_enum": "RED"}, 0, "BLUE", False),
        ({"field_enum": "BLUE"}, 0, "BLUE", True),
        ({}, 1, "HR_007", True),
        ({"resolution": "HR"}, 1, "HR_007", True),
        ({"resolution": "LR"}, 1, "HR_007", False),
        ({"field_i": 7}, 1, "HR_007", True),
        ({"field_i": 12}, 1, "HR_007", False),
        ({}, 1, "M", True),
        ({"field_size": "M"}, 1, "M", True),
        ({"field_size": "L"}, 1, "M", False),
        ({}, 2, "HR_007", True),
        ({"resolution": "HR"}, 2, "HR_007", True),
        ({"resolution": "LR"}, 2, "HR_007", False),
        ({"field_i": 7}, 2, "HR_007", True),
        ({"field_i": 12}, 2, "HR_007", False),
    ],
)
def test_composite_layout_test(
    composite_layout: CompositeLayout,
    filters: dict[str, tp.tp.Any],
    level: int,
    node: str,
    expected: bool,
):
    composite_layout.set_filters(**filters)
    assert composite_layout.test(level, node) is expected


@pytest.mark.parametrize(
    "level, node",
    [
        (0, "foo"),
        (1, "bar"),
    ],
)
def test_composite_layout_warn(
    composite_layout: CompositeLayout, level: int, node: str
):
    composite_layout.set_filters()
    with pytest.warns(UserWarning):
        assert not composite_layout.test(level, node)


def test_composite_layout_unknown_filters(composite_layout: CompositeLayout):
    with pytest.warns(UserWarning):
        composite_layout.set_filters(foo="bar")


@pytest.fixture(scope="session")
def memory_fs(filepaths: list[str]) -> MemoryFileSystem:
    fs = MemoryFileSystem()
    fs.mkdir("/folder")
    for filepath in filepaths:
        filepath = Path(filepath)
        fs.touch(f"/folder/{filepath.name}")

        fs.makedirs(filepath.parent, exist_ok=True)
        fs.touch(filepath)
    return fs


def test_file_system_tree_find(memory_fs: MemoryFileSystem):
    it = FileSystemIterable(memory_fs)
    assert list(it.find("/folder")) == memory_fs.find("/folder")


def test_file_system_tree_unknown_filter(memory_fs: MemoryFileSystem):
    it = FileSystemIterable(memory_fs)
    with pytest.warns(UserWarning):
        next(it.find("/folder", dummy="baz"))


def test_file_system_tree_layout_find_in_flattened(
    memory_fs: MemoryFileSystem, layout: Layout
):
    it = FileSystemIterable(memory_fs)
    it_layout = FileSystemIterable(memory_fs, layout)

    assert len(list(it.find("/folder"))) == len(list(it_layout.find("/root")))
    assert set(it.find("/folder")) == set(it_layout.find("/folder"))


def test_file_system_tree_layout_discrepency(
    memory_fs: MemoryFileSystem, layout: Layout
):
    it_layout = FileSystemIterable(memory_fs, layout)

    # Nothing is found because all folders are eliminated from the search. The
    # layout should give us hints about the mismatch
    with pytest.warns(UserWarning):
        assert len(list(it_layout.find("/root/RED", field_i=1))) == 0


def test_file_system_tree_layout_common_filters(
    memory_fs: MemoryFileSystem, layout: Layout, filepaths: list[str]
):
    it_layout = FileSystemIterable(memory_fs, layout)
    expected = [Path(x).name for ii, x in enumerate(filepaths) if ii in [1, 4, 5]]
    actual = sorted([Path(x).name for x in it_layout.find("/root", field_i=[1, 4, 5])])
    assert actual == expected


def test_file_system_tree_layout_independent_filter(
    memory_fs: MemoryFileSystem, layout: Layout, filepaths: list[str]
):
    it_layout = FileSystemIterable(memory_fs, layout)
    expected = [Path(x).name for ii, x in enumerate(filepaths) if ii in [1, 4, 5]]
    actual = sorted(
        [
            Path(x).name
            for x in it_layout.find(
                "/root", resolution="LR", field_i=[1, 4, 5, 6, 7, 8]
            )
        ]
    )
    assert actual == expected


def test_file_system_tree_layout_unknown_filter(
    memory_fs: MemoryFileSystem, layout: Layout
):
    it_layout = FileSystemIterable(memory_fs, layout)
    with pytest.warns(UserWarning):
        next(it_layout.find("/root", dummy="bar"))


def test_file_system_tree_layout_details(memory_fs: MemoryFileSystem, layout: Layout):
    it_layout = FileSystemIterable(memory_fs, layout)
    detailed = list(it_layout.find("/root", resolution="LR", detail=True))
    simple = set(it_layout.find("/root", resolution="LR", detail=False))

    assert detailed[0].keys() == {"name", "size", "type", "created"}
    assert {x["name"] for x in detailed} == simple


@pytest.fixture
def discoverer(
    convention: FileNameConvention, memory_fs: MemoryFileSystem, layout: Layout
) -> FileDiscoverer:
    return FileDiscoverer(convention, FileSystemIterable(memory_fs, layout))


@pytest.mark.parametrize(
    "filters, expected_selection",
    [
        (dict(field_enum=Color.RED, field_f=1.75), [3]),
        (
            dict(
                field_period=Period(
                    np.datetime64("2011-01-01"), np.datetime64("2013-12-31")
                )
            ),
            list(range(6)),
        ),
        (
            dict(
                field_date=Period(
                    np.datetime64("2023-02-03"), np.datetime64("2023-02-08")
                ),
                field_s="baz",
            ),
            [6, 7],
        ),
        (dict(field_f=0.25, field_date_delta=np.datetime64("1950-01-01")), []),
        (dict(resolution="HR", field_i=list(range(0, 10, 2))), [6, 8]),
        (dict(predicates=[lambda record: record[0] in [0, 3]]), [0, 3]),
    ],
)
def test_file_discoverer(discoverer, filters, expected_selection):
    df = discoverer.list("/root", **filters)
    assert np.array_equal(sorted(df["field_i"].values), expected_selection)
    assert "filename" in df.columns


def test_file_discoverer_stat_fields(discoverer):
    df = discoverer.list("/folder", stat_fields=("size", "type"))
    assert np.array_equal(df["size"].values, np.full(9, fill_value=0))
    assert np.array_equal(df["type"].values, np.full(9, fill_value="file"))


def test_file_discoverer_stat_fields_error(discoverer):
    with pytest.raises(KeyError):
        discoverer.list("/folder", stat_fields=("foo",))


def test_file_discoverer_no_layout(
    discoverer: FileDiscoverer, memory_fs: MemoryFileSystem
):
    discoverer_no_layout = FileDiscoverer(
        discoverer.convention, FileSystemIterable(memory_fs)
    )
    df_ref = discoverer.list("/root", field_f=0.25)
    assert len(df_ref) > 0

    df_actual = discoverer_no_layout.list("/root", field_f=0.25)
    assert df_ref.equals(df_actual)
