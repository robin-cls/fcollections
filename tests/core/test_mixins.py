import numpy as np
import pandas as pda
import pytest

from fcollections.core import DiscreteTimesMixin, PeriodMixin
from fcollections.time import Period


class PeriodMixinEmpty(PeriodMixin):

    def list_files(self, *args, **kwargs):
        return pda.DataFrame([], columns=['time', 'filename'])


def test_period_mixin_empty():
    mixin = PeriodMixinEmpty()
    assert mixin.time_coverage() is None
    assert len(list(mixin.time_holes())) == 0


class PeriodMixinStub(PeriodMixin):

    def list_files(self, *args, **kwargs):
        return pda.DataFrame([(Period(np.datetime64('2024-01-01'),
                                      np.datetime64('2024-01-02'),
                                      include_stop=False), 'f1'),
                              (Period(np.datetime64('2024-01-02'),
                                      np.datetime64('2024-01-03'),
                                      include_stop=False), 'f2'),
                              (Period(np.datetime64('2024-01-04'),
                                      np.datetime64('2024-01-05'),
                                      include_stop=False), 'f3'),
                              (Period(np.datetime64('2024-01-10'),
                                      np.datetime64('2024-01-20'),
                                      include_start=False,
                                      include_stop=False), 'f4')],
                             columns=['time', 'filename'])


def test_period_mixin():
    mixin = PeriodMixinStub()
    assert mixin.time_coverage() == Period(np.datetime64('2024-01-01'),
                                           np.datetime64('2024-01-20'),
                                           include_stop=False)
    assert list(mixin.time_holes()) == [
        Period(np.datetime64('2024-01-03'),
               np.datetime64('2024-01-04'),
               include_stop=False),
        Period(np.datetime64('2024-01-05'), np.datetime64('2024-01-10'))
    ]


class DiscreteTimesEmpty(DiscreteTimesMixin):

    def list_files(self, *args, **kwargs):
        return pda.DataFrame([], columns=['time', 'filename'])


def test_discrete_times_mixin_empty():
    mixin = DiscreteTimesEmpty(np.timedelta64(1, 'D'))
    assert mixin.time_coverage() is None
    assert len(list(mixin.time_holes())) == 0


class DiscreteTimesStub(DiscreteTimesMixin):

    def list_files(self, *args, **kwargs):
        return pda.DataFrame([
            (np.datetime64('2024-01-01'), 'f1'),
            (np.datetime64('2024-01-02'), 'f2'),
            (np.datetime64('2024-01-04'), 'f3'),
            (np.datetime64('2024-01-10'), 'f4'),
        ],
                             columns=['time', 'filename'])


def test_discrete_times_mixin():
    mixin = DiscreteTimesStub(np.timedelta64(1, 'D'))
    assert mixin.time_coverage() == Period(np.datetime64('2024-01-01'),
                                           np.datetime64('2024-01-10'))
    assert list(mixin.time_holes()) == [
        Period(np.datetime64('2024-01-02'),
               np.datetime64('2024-01-04'),
               include_start=False,
               include_stop=False),
        Period(np.datetime64('2024-01-04'),
               np.datetime64('2024-01-10'),
               include_start=False,
               include_stop=False)
    ]


def test_discrete_times_mixin_no_sampling():
    mixin = DiscreteTimesStub()
    assert mixin.time_coverage() == Period(np.datetime64('2024-01-01'),
                                           np.datetime64('2024-01-10'))
    with pytest.warns(UserWarning):
        assert list(mixin.time_holes()) == []
