"""Tests for MySolensoStationData — detailed station configuration."""

import pytest
from unittest.mock import MagicMock, patch

from mysolenso.services.stationdata import MySolensoStationData
from mysolenso.exceptions import MySolensoException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STATION_DETAIL = {
    "name":              "Solar Roof",
    "create_at":         "2024-01-01",
    "capacitor":         "3.0",
    "address":           "1 rue de la Paix, Paris",
    "config":            {"key": "value"},
    "is_stars":          1,
    "money_unit":        "EUR",
    "electricity_price": 0.174,
    "timezone":          {"name": "Europe/Paris", "offset": 1},
    "local_time":        "2026-05-15 10:32:00",
    "group":     {
                    "id": 123456,
                    "name": "Install Solenso",
                    "pid": 111139,
                    "type": 4,
                    "contact": "John Solenso",
                    "phone": "+33700000000",
                    "area": "",
                    "icon": ""
                },
}


def _make_stationdata(api_data: dict, station_id: int = 42) -> MySolensoStationData:
    parent = MagicMock()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "tok"}
    parent.station.station_id = station_id
    parent.station.stations   = [{"id": station_id, "ak": "ak_abc"}]
    with patch("mysolenso.services.stationdata.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = api_data
        return MySolensoStationData(parent)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

def test_stationdata_station_id():
    sd = _make_stationdata(STATION_DETAIL)
    assert sd.station_id == 42


def test_stationdata_name():
    sd = _make_stationdata(STATION_DETAIL)
    assert sd.name == "Solar Roof"


def test_stationdata_create_at():
    sd = _make_stationdata(STATION_DETAIL)
    assert sd.create_at == "2024-01-01"


def test_stationdata_capacitor():
    sd = _make_stationdata(STATION_DETAIL)
    assert sd.capacitor == "3.0"


def test_stationdata_address():
    sd = _make_stationdata(STATION_DETAIL)
    assert sd.address == "1 rue de la Paix, Paris"


def test_stationdata_config():
    sd = _make_stationdata(STATION_DETAIL)
    assert sd.config == {"key": "value"}


def test_stationdata_is_stars():
    sd = _make_stationdata(STATION_DETAIL)
    assert sd.is_stars == 1


def test_stationdata_money_unit():
    sd = _make_stationdata(STATION_DETAIL)
    assert sd.money_unit == "EUR"


def test_stationdata_electricity_price():
    sd = _make_stationdata(STATION_DETAIL)
    assert sd.electricity_price == pytest.approx(0.174)


def test_stationdata_timezone():
    sd = _make_stationdata(STATION_DETAIL)
    assert sd.timezone == {"name": "Europe/Paris", "offset": 1}


def test_stationdata_local_time():
    sd = _make_stationdata(STATION_DETAIL)
    assert sd.local_time == "2026-05-15 10:32:00"


def test_stationdata_install_power():
    sd = _make_stationdata(STATION_DETAIL)
    assert sd.install_power == {
                    "id": 123456,
                    "name": "Install Solenso",
                    "pid": 111139,
                    "type": 4,
                    "contact": "John Solenso",
                    "phone": "+33700000000",
                    "area": "",
                    "icon": ""
                }


def test_stationdata_all_data():
    sd = _make_stationdata(STATION_DETAIL)
    assert sd.all_data == STATION_DETAIL


# ---------------------------------------------------------------------------
# is_stars does not recurse (bug-fix regression)
# ---------------------------------------------------------------------------

def test_is_stars_no_infinite_recursion():
    """Accessing is_stars must not raise RecursionError."""
    sd = _make_stationdata({**STATION_DETAIL, "is_stars": 0})
    # Should complete without hitting Python's recursion limit
    result = sd.is_stars
    assert result == 0


# ---------------------------------------------------------------------------
# Missing / None station_id
# ---------------------------------------------------------------------------

def test_stationdata_none_station_id_raises():
    """station_id=None on parent raises MySolensoException."""
    parent = MagicMock()
    parent.station.station_id = None
    with pytest.raises(MySolensoException):
        MySolensoStationData(parent)


# ---------------------------------------------------------------------------
# set_station_find
# ---------------------------------------------------------------------------

def test_set_station_find_valid():
    """set_station_find switches station and reloads data."""
    parent = MagicMock()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "tok"}
    parent.station.station_id = 42
    parent.station.stations   = [{"id": 42, "ak": "a"}, {"id": 43, "ak": "b"}]

    with patch("mysolenso.services.stationdata.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = STATION_DETAIL
        sd = MySolensoStationData(parent)

        # Switch to station 43
        MockPost.return_value.post.return_value = {**STATION_DETAIL, "name": "Garden Panel"}
        sd.set_station_find(43)

    assert sd.station_id == 43
    assert sd.name == "Garden Panel"


def test_set_station_find_invalid_raises():
    """set_station_find with unknown ID raises MySolensoException."""
    sd = _make_stationdata(STATION_DETAIL)

    with pytest.raises(MySolensoException):
        sd.set_station_find(999)


# ---------------------------------------------------------------------------
# API error handling
# ---------------------------------------------------------------------------

def test_api_error_raises():
    """Network error during construction raises MySolensoException."""
    parent = MagicMock()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "tok"}
    parent.station.station_id = 42
    with patch("mysolenso.services.stationdata.MySolensoPost") as MockPost:
        MockPost.return_value.post.side_effect = Exception("timeout")
        with pytest.raises(MySolensoException):
            MySolensoStationData(parent)


def test_missing_fields_return_none():
    """Fields absent from the API response return None."""
    sd = _make_stationdata({})
    assert sd.name is None
    assert sd.electricity_price is None
    assert sd.install_power is None
