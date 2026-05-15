"""Tests for MySolensoStationCount — detailed station configuration."""

import pytest
from unittest.mock import MagicMock, patch

from mysolenso.services.stationcount import MySolensoStationCount
from mysolenso.exceptions import MySolensoException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STATION_DETAIL = {
                "is_null": 0,
                "today_eq": "17647.0",
                "month_eq": "241047",
                "year_eq": "1769064",
                "total_eq": "14685977",
                "real_power": "0",
                "co2_emission_reduction": "14641919.069",
                "plant_tree": "800",
                "data_time": "2026-05-14 21:20:06",
                "last_data_time": "2026-05-14 21:20:06",
                "capacitor": "5",
                "is_balance": 0,
                "is_reflux": 0,
                "pv2": 0,
                "clp": 200
            }


def _make_stationcount(api_data: dict, station_id: int = 42) -> MySolensoStationCount:
    parent = MagicMock()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "tok"}
    parent.station.station_id = station_id
    parent.station.stations   = [{"id": station_id, "ak": "ak_abc"}]
    with patch("mysolenso.services.stationcount.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = api_data
        return MySolensoStationCount(parent)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

def test_stationcount_all_data():
    sd = _make_stationcount(STATION_DETAIL)
    assert sd.all_data == STATION_DETAIL
    
def test_stationcount_station_id():
    sd = _make_stationcount(STATION_DETAIL)
    assert sd.station_id == 42


def test_stationcount_today_eq():
    sd = _make_stationcount(STATION_DETAIL)
    assert sd.today_eq == "17647.0"


def test_stationcount_month_eq():
    sd = _make_stationcount(STATION_DETAIL)
    assert sd.month_eq == "241047"


def test_stationcount_year_eq():
    sd = _make_stationcount(STATION_DETAIL)
    assert sd.year_eq == "1769064"


def test_stationcount_total_eq():
    sd = _make_stationcount(STATION_DETAIL)
    assert sd.total_eq == "14685977"


def test_stationcount_real_power():
    sd = _make_stationcount(STATION_DETAIL)
    assert sd.real_power == "0"


def test_stationcount_co2_emission_reduction():
    sd = _make_stationcount(STATION_DETAIL)
    assert sd.co2_emission_reduction == "14641919.069"


def test_stationcount_plant_tree():
    sd = _make_stationcount(STATION_DETAIL)
    assert sd.plant_tree == "800"


def test_stationcount_data_time():
    sd = _make_stationcount(STATION_DETAIL)
    assert sd.data_time == "2026-05-14 21:20:06"


def test_stationcount_last_data_time():
    sd = _make_stationcount(STATION_DETAIL)
    assert sd.last_data_time == "2026-05-14 21:20:06"


def test_stationcount_capacitor():
    sd = _make_stationcount(STATION_DETAIL)
    assert sd.capacitor == "5"

# ---------------------------------------------------------------------------
# Missing / None station_id
# ---------------------------------------------------------------------------

def test_stationcount_none_station_id_raises():
    """station_id=None on parent raises MySolensoException."""
    parent = MagicMock()
    parent.station.station_id = None
    with pytest.raises(MySolensoException):
        MySolensoStationCount(parent)


# ---------------------------------------------------------------------------
# set_station_count
# ---------------------------------------------------------------------------

def test_set_station_count_valid():
    """set_station_count switches station and reloads data."""
    parent = MagicMock()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "tok"}
    parent.station.station_id = 42
    parent.station.stations   = [{"id": 42, "ak": "a"}, {"id": 43, "ak": "b"}]

    with patch("mysolenso.services.stationcount.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = STATION_DETAIL
        sd = MySolensoStationCount(parent)

        # Switch to station 43
        MockPost.return_value.post.return_value = {**STATION_DETAIL, "today_eq": "572.0"}
        sd.set_station_count(43)

    assert sd.station_id == 43
    assert sd.today_eq == "572.0"


def test_set_station_count_invalid_raises():
    """set_station_count with unknown ID raises MySolensoException."""
    sd = _make_stationcount(STATION_DETAIL)

    with pytest.raises(MySolensoException):
        sd.set_station_count(999)


# ---------------------------------------------------------------------------
# API error handling
# ---------------------------------------------------------------------------

def test_api_error_raises():
    """Network error during construction raises MySolensoException."""
    parent = MagicMock()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "tok"}
    parent.station.station_id = 42
    with patch("mysolenso.services.stationcount.MySolensoPost") as MockPost:
        MockPost.return_value.post.side_effect = Exception("timeout")
        with pytest.raises(MySolensoException):
            MySolensoStationCount(parent)


def test_missing_fields_return_none():
    """Fields absent from the API response return None."""
    sd = _make_stationcount({})
    assert sd.today_eq is None
    assert sd.month_eq is None
    assert sd.year_eq is None
