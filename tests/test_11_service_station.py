"""Tests for MySolensoStation - PV station list and selection."""

import pytest
from unittest.mock import MagicMock, patch

from mysolenso.services.station import MySolensoStation
from mysolenso.exceptions import MySolensoException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STATION_1 = {
    "id": 42, "ak": "ak_abc", "name": "Solar Roof",
    "city_code": "75001", "status": 1,
    "create_at": "2024-01-01", "tz_name": "Europe/Paris",
    "capacitor": "3.0", "install_power": "3000",
    "address": "1 rue de la Paix, Paris",
    "org_name": "My Org", "warn_data": {}, "ak": "ak_abc",
}
STATION_2 = {
    "id": 43, "ak": "ak_def", "name": "Garden Panel",
    "city_code": "69001", "status": 1,
    "create_at": "2024-06-01", "tz_name": "Europe/Paris",
    "capacitor": "1.5", "install_power": "1500",
    "address": "2 rue Carnot, Lyon",
    "org_name": "My Org", "warn_data": {}, "ak": "ak_def",
}


def _make_station(api_list: list, total: int = None) -> MySolensoStation:
    """Build a MySolensoStation with a mocked POST response."""
    parent = MagicMock()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "tok"}
    with patch("mysolenso.services.station.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = {
            "total": total if total is not None else len(api_list),
            "list":  api_list,
        }
        return MySolensoStation(parent)


# ---------------------------------------------------------------------------
# Single station
# ---------------------------------------------------------------------------

def test_station_total_single():
    st = _make_station([STATION_1])
    assert st.station_total == 1


def test_station_id_single():
    st = _make_station([STATION_1])
    assert st.station_id == 42


def test_station_name_single():
    st = _make_station([STATION_1])
    assert st.name == "Solar Roof"


def test_station_install_power():
    st = _make_station([STATION_1])
    assert st.install_power == "3000"


def test_station_address():
    st = _make_station([STATION_1])
    assert st.address == "1 rue de la Paix, Paris"


def test_station_ak():
    st = _make_station([STATION_1])
    assert st.ak == "ak_abc"


def test_station_status():
    st = _make_station([STATION_1])
    assert st.status == 1


def test_station_tz_name():
    st = _make_station([STATION_1])
    assert st.tz_name == "Europe/Paris"


# ---------------------------------------------------------------------------
# Multiple stations
# ---------------------------------------------------------------------------

def test_station_total_multiple():
    st = _make_station([STATION_1, STATION_2])
    assert st.station_total == 2


def test_station_defaults_to_first():
    st = _make_station([STATION_1, STATION_2])
    assert st.station_id == 42


def test_station_ids_multiple():
    st = _make_station([STATION_1, STATION_2])
    assert st.station_ids == [42, 43]


def test_stations_summary():
    st = _make_station([STATION_1, STATION_2])
    assert st.stations == [{"id": 42, "ak": "ak_abc"}, {"id": 43, "ak": "ak_def"}]


def test_set_station_switches_active():
    st = _make_station([STATION_1, STATION_2])
    st.set_station(2)

    assert st.station_id == 43
    assert st.name == "Garden Panel"
    assert st.install_power == "1500"


def test_set_station_back_to_first():
    st = _make_station([STATION_1, STATION_2])
    st.set_station(2)
    st.set_station(1)

    assert st.station_id == 42


def test_set_station_out_of_range_raises():
    st = _make_station([STATION_1, STATION_2])

    with pytest.raises(MySolensoException):
        st.set_station(3)


def test_set_station_zero_raises():
    st = _make_station([STATION_1])

    with pytest.raises(MySolensoException):
        st.set_station(0)


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_no_stations_raises():
    """total=0 raises MySolensoException during construction."""
    parent = MagicMock()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "tok"}
    with patch("mysolenso.services.station.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = {"total": 0, "list": []}
        with pytest.raises(MySolensoException):
            MySolensoStation(parent)


def test_api_error_raises():
    """Network error during construction raises MySolensoException."""
    parent = MagicMock()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "tok"}
    with patch("mysolenso.services.station.MySolensoPost") as MockPost:
        MockPost.return_value.post.side_effect = Exception("timeout")
        with pytest.raises(MySolensoException):
            MySolensoStation(parent)


# ---------------------------------------------------------------------------
# all_data and refresh
# ---------------------------------------------------------------------------

def test_all_data_returns_list():
    st = _make_station([STATION_1, STATION_2])
    assert isinstance(st.all_data, list)
    assert len(st.all_data) == 2


def test_refresh_station_reloads_from_cache():
    """refresh_station() re-reads attributes without a network call."""
    st = _make_station([STATION_1])
    original_name = st.name

    # Manually corrupt a private attr then refresh
    st._all_data[0]["name"] = "Patched Name"
    st.refresh_station()

    assert st.name == "Patched Name"
    assert original_name == "Solar Roof"
