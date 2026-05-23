"""Tests for MySolensoPowerPlayBackByDay - intra-day power playback service."""

import re
import struct
import pytest
from unittest.mock import MagicMock, patch

from mysolenso.services.stations.powerbyday import MySolensoPowerPlayBackByDay
from mysolenso.exceptions import MySolensoException


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

POWER_TIMES = ["06:00", "06:15", "06:30"]
POWER_VALUES = [26.6, 63.4, 110.3]


def _build_protobuf_response(date: str, times: list, powers: list) -> bytes:
    """Build a minimal fake binary response that mimics the Hoymiles format.

    Layout: date bytes, then for each time label ``\\x12<len><HH:MM>``,
    then the packed float32 values concatenated.
    """
    buf = b""
    buf += date.encode()
    for t in times:
        enc = t.encode()
        buf += b"\x12" + bytes([len(enc)]) + enc
    for p in powers:
        buf += struct.pack("<f", p)
    return buf


POWER_RESPONSE = _build_protobuf_response("2026-05-23", POWER_TIMES, POWER_VALUES)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_parent(station_id=42, stations=None):
    """Return a minimal MagicMock parent with station and auth context."""
    parent = MagicMock()
    parent.station.station_id = station_id
    parent.station.stations = stations or [{"id": station_id}]
    parent.auth.get_auth_headers_hoymiles.return_value = {"Cookie": "hoymiles_token=tok"}
    return parent


def _make_power(api_response: bytes = None) -> MySolensoPowerPlayBackByDay:
    parent = _make_parent()
    response = api_response if api_response is not None else POWER_RESPONSE
    with patch("mysolenso.services.stations.powerbyday.MySolensoPost") as MockPost:
        MockPost.return_value.poststr.return_value = response
        obj = MySolensoPowerPlayBackByDay(parent)
        obj._get_power_playback_by_day()
        return obj


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestMySolensoPowerPlayBackByDayInit:
    """Construction and validation."""

    def test_raises_when_no_station(self):
        """Constructor raises MySolensoException when station_id is None."""
        parent = _make_parent(station_id=None)
        with pytest.raises(MySolensoException):
            MySolensoPowerPlayBackByDay(parent)

    def test_stores_station_id(self):
        """Constructor stores the station_id from the parent."""
        parent = _make_parent(station_id=55)
        obj = MySolensoPowerPlayBackByDay(parent)
        assert obj._station_id == 55

    def test_default_day_is_set(self):
        """A default day string in YYYY-MM-DD format is set at construction."""
        parent = _make_parent()
        obj = MySolensoPowerPlayBackByDay(parent)
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", obj.day)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

class TestMySolensoPowerPlayBackByDayProperties:
    """Property accessors."""

    def test_get_data_contains_date_key(self):
        obj = _make_power()
        assert "date" in obj.get_data

    def test_get_data_contains_values_key(self):
        obj = _make_power()
        assert "values" in obj.get_data

    def test_get_data_date_value(self):
        obj = _make_power()
        assert obj.get_data["date"] == "2026-05-23"

    def test_get_data_time_labels_present(self):
        obj = _make_power()
        values = obj.get_data["values"]
        for t in POWER_TIMES:
            assert t in values

    def test_get_data_power_values_are_floats(self):
        obj = _make_power()
        for v in obj.get_data["values"].values():
            assert isinstance(v, float)

    def test_day_property(self):
        parent = _make_parent()
        obj = MySolensoPowerPlayBackByDay(parent)
        assert obj.day == obj._day


# ---------------------------------------------------------------------------
# set_day
# ---------------------------------------------------------------------------

class TestMySolensoPowerPlayBackByDaySetDay:
    """set_day validation."""

    def test_set_day_invalid_format_raises(self):
        parent = _make_parent()
        obj = MySolensoPowerPlayBackByDay(parent)
        with pytest.raises(MySolensoException):
            obj.set_day("not-a-date", refresh=False)

    def test_set_day_future_date_raises(self):
        parent = _make_parent()
        obj = MySolensoPowerPlayBackByDay(parent)
        with pytest.raises(MySolensoException):
            obj.set_day("2999-12-31", refresh=False)

    def test_set_day_valid_stores_day(self):
        parent = _make_parent()
        obj = MySolensoPowerPlayBackByDay(parent)
        obj.set_day("2025-01-15", refresh=False)
        assert obj._day == "2025-01-15"

    def test_set_day_with_refresh_calls_api(self):
        """set_day with refresh=True triggers a new API call."""
        parent = _make_parent()
        with patch("mysolenso.services.stations.powerbyday.MySolensoPost") as MockPost:
            MockPost.return_value.poststr.return_value = POWER_RESPONSE
            obj = MySolensoPowerPlayBackByDay(parent)
            obj._get_power_playback_by_day()
            count_before = MockPost.return_value.poststr.call_count
            obj.set_day("2025-06-01", refresh=True)
            assert MockPost.return_value.poststr.call_count > count_before


# ---------------------------------------------------------------------------
# set_station_id
# ---------------------------------------------------------------------------

class TestMySolensoPowerPlayBackByDaySetStation:
    """set_station_id behaviour."""

    def test_set_station_invalid_raises(self):
        """set_station_id raises when the station ID is not in the account list."""
        parent = _make_parent(station_id=42, stations=[{"id": 42}])
        obj = MySolensoPowerPlayBackByDay(parent)
        with pytest.raises(MySolensoException):
            obj.set_station_id(9999, refresh=False)

    def test_set_station_updates_id(self):
        """set_station_id stores the new station ID."""
        parent = _make_parent(station_id=42, stations=[{"id": 42}, {"id": 43}])
        obj = MySolensoPowerPlayBackByDay(parent)
        obj.set_station_id(43, refresh=False)
        assert obj._station_id == 43

    def test_set_station_with_refresh_calls_api(self):
        """set_station_id with refresh=True triggers a new API call."""
        parent = _make_parent(station_id=42, stations=[{"id": 42}, {"id": 43}])
        with patch("mysolenso.services.stations.powerbyday.MySolensoPost") as MockPost:
            MockPost.return_value.poststr.return_value = POWER_RESPONSE
            obj = MySolensoPowerPlayBackByDay(parent)
            obj._get_power_playback_by_day()
            count_before = MockPost.return_value.poststr.call_count
            obj.set_station_id(43, refresh=True)
            assert MockPost.return_value.poststr.call_count > count_before


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestMySolensoPowerPlayBackByDayErrors:
    """Error handling."""

    def test_network_error_raises(self):
        parent = _make_parent()
        with patch("mysolenso.services.stations.powerbyday.MySolensoPost") as MockPost:
            MockPost.return_value.poststr.side_effect = Exception("timeout")
            obj = MySolensoPowerPlayBackByDay(parent)
            with pytest.raises(MySolensoException):
                obj._get_power_playback_by_day()

    def test_get_power_refresh_calls_api(self):
        parent = _make_parent()
        with patch("mysolenso.services.stations.powerbyday.MySolensoPost") as MockPost:
            MockPost.return_value.poststr.return_value = POWER_RESPONSE
            obj = MySolensoPowerPlayBackByDay(parent)
            obj._get_power_playback_by_day()
            obj.get_power_refresh()
            assert MockPost.return_value.poststr.call_count >= 2

    def test_headers_injected(self):
        """Hoymiles auth headers are passed to the HTTP client."""
        parent = _make_parent()
        parent.auth.get_auth_headers_hoymiles.return_value = {"Cookie": "hoymiles_token=xyz"}
        with patch("mysolenso.services.stations.powerbyday.MySolensoPost") as MockPost:
            MockPost.return_value.poststr.return_value = POWER_RESPONSE
            obj = MySolensoPowerPlayBackByDay(parent)
            obj._get_power_playback_by_day()
            MockPost.return_value.set_headers.assert_called_with({"Cookie": "hoymiles_token=xyz"})
