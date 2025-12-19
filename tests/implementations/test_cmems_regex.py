import re

import pytest

from fcollections.implementations._definitions._cmems import build_convention


@pytest.mark.parametrize(
    "dataset_id",
    [
        # SST_GLO_SST_L3S_NRT_OBSERVATIONS_010_010
        "cmems_obs-sst_glo_phy_l3s_gir_P1D-m",
        "IFREMER-GLOB-SST-L3-NRT-OBS_FULL_TIME_SERIE",
        "cmems_obs-sst_glo_phy_l3s_pir_P1D-m",
        "cmems_obs-sst_glo_phy_l3s_pmw_P1D-m",
    ],
)
def test_regex_match(dataset_id: str):
    convention = build_convention()
    actual = convention.regex.match(dataset_id)
    assert actual is not None
