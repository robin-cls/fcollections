from __future__ import annotations

import typing as tp

import numpy as np
import pytest
import xarray as xr

if tp.TYPE_CHECKING:
    from pathlib import Path

    import numpy.typing as np_t


def _build_along_track(
    lon: np_t.NDArray[np.int64 | np.float64],
    lat: np_t.NDArray[np.int64 | np.float64],
    lon_name: str = "longitude",
    lat_name: str = "latitude",
) -> xr.Dataset:
    np.random.seed(0)
    ds = xr.Dataset()

    ds[lon_name] = (["time"], lon)
    ds[lat_name] = (["time"], lat)

    time = np.arange("2024-01-01T12", "2024-01-01T16", dtype="M8[h]")
    ds["time"] = (
        ["time"],
        time.astype("datetime64[ns]"),
    )
    sla = np.random.random(lon.size)
    ds["sla"] = (["time"], sla)
    ds = ds.set_coords([lon_name, lat_name, "time"]).astype(np.float32)
    return ds


@pytest.fixture(scope="session")
def l3_nadir_dataset_0_360() -> xr.Dataset:
    lon, lat = np.array([1, 2, 358, 359]), np.array([1, 2, 3, 4])
    return _build_along_track(lon, lat)


@pytest.fixture(scope="session")
def l3_nadir_dataset_180_180() -> xr.Dataset:
    lon, lat = np.array([-1, 0, 1, 2]), np.array([-1, 0, 1, 2])
    return _build_along_track(lon, lat)


# /work/HELPDESK_SWOTLR/commun/data/cmems/SEALEVEL_GLO_PHY_L3_MY_008_062/
#
@pytest.fixture(scope="session")
def l3_nadir_files() -> list[str]:
    return [
        "cmems_obs-sl_glo_phy-ssh_nrt_j3g-l3-duacs_PT0.2S-i_202411/2022/06/nrt_global_j3g_phy_l3_5hz_20220617_20240205.nc",
        "cmems_obs-sl_glo_phy-ssh_nrt_j3g-l3-duacs_PT0.2S_202512/2025/07/nrt_global_j3g_phy_l3_5hz_20250702_20250710.nc",
        "cmems_obs-sl_glo_phy-ssh_nrt_s3a-l3-duacs_PT0.2S_202411/2022/06/nrt_global_s3a_phy_l3_5hz_20220617_20240205.nc",
        "cmems_obs-sl_glo_phy-ssh_nrt_s3a-l3-duacs_PT0.2S_202411/2022/06/nrt_global_s3a_phy_l3_5hz_20220617_20240205.nc",
        "cmems_obs-sl_glo_phy-ssh_nrt_s3a-l3-duacs_PT1S_202411/2022/06/nrt_global_s3a_phy_l3_1hz_20220617_20240205.nc",
        "cmems_obs-sl_glo_phy-ssh_my_c2n-l3-duacs_PT1S_202512/2022/06/dt_global_c2n_phy_l3_1hz_20220617_20240205.nc",
        "cmems_obs-sl_glo_phy-ssh_my_c2n-l3-duacs_PT1S_202411/2022/06/dt_global_c2n_phy_l3_1hz_20220617_20240205.nc",
        "cmems_obs-sl_glo_phy-ssh_my_s6a-hr-l3-duacs_PT1S_202211/2020/02/dt_global_s6a_hr_phy_l3_1hz_20200217_20221105.nc",
        "cmems_obs-sl_glo_phy-ssh_my_s6a-lr-l3-duacs_PT1S_202211/2020/02/dt_global_s6a_lr_phy_l3_1hz_20200218_20221105.nc",
    ]


@pytest.fixture(scope="session")
def l3_nadir_dir_layout(
    tmp_path_factory: pytest.TempPathFactory, l3_nadir_files: list[str]
) -> Path:
    root = tmp_path_factory.mktemp("SEALEVEL_GLO_PHY_L3_NRT_008_044")

    # create test folder
    for filepath in l3_nadir_files:
        filepath = root / filepath

        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.touch()

    return root


@pytest.fixture(scope="session")
def l3_nadir_files_2() -> list[str]:
    return [
        "nrt_global_al_phy_l3_20231014_20231103.nc",
        "nrt_global_swonc_phy_l3_1hz_20230209_20230302.nc",
        "nrt_global_swonc_phy_l3_1hz_20231003_20231024.nc",
    ]


@pytest.fixture(scope="session")
def l3_nadir_dir(
    tmp_path_factory: pytest.TempPathFactory,
    l3_nadir_files_2: list[str],
    l3_nadir_dataset_0_360: xr.Dataset,
) -> Path:
    # create test folder
    test_dir = tmp_path_factory.mktemp("test_dir")

    # create test files
    for file in l3_nadir_files_2:
        f = test_dir / file
        l3_nadir_dataset_0_360.to_netcdf(f)

    return test_dir


@pytest.fixture(scope="session")
def l2_nadir_files() -> list[str]:
    return [
        "SWOT_IPN_2PfP575_015_20230707_181108_20230707_190214.nc",
        "SWOT_GPN_2PfP575_014_20230707_172003_20230707_181108.nc",
        "SWOT_GPN_2PfP574_014_20230706_172925_20230706_182030.nc",
    ]


@pytest.fixture(scope="session")
def l2_nadir_dir(
    tmp_path_factory: pytest.TempPathFactory, l2_nadir_files: list[str]
) -> Path:
    # create test folder
    test_dir = tmp_path_factory.mktemp("test_dir")

    # create test files
    for file in l2_nadir_files:
        f = test_dir / file
        f.touch()

    return test_dir
