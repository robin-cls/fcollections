import re

import pytest

from fcollections.implementations._definitions._cmems import build_convention


@pytest.mark.parametrize(
    "dataset_id",
    [
        # WAVE_GLO_PHY_SWH_L3_NRT_014_001
        "cmems_obs-wave_glo_phy-swh_nrt_cfo-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_c2-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_h2b-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_h2c-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_j3-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_al-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_s3a-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_s3b-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_s6a-l3_PT1S",
        "cmems_obs-wave_glo_phy-swh_nrt_swon-l3_PT1S",
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
