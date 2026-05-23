"""Tests for MySolensoStationDataModuleDay - daily module data download descriptor service."""

import re
import pytest
from unittest.mock import MagicMock, patch

from mysolenso.services.stations.datamodule import MySolensoStationDataModuleDay
from mysolenso.exceptions import MySolensoException


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

DATAMODULE_RESPONSE = [
    {
        "sid": 1553580,
        "date": "2026-05-12",
        "url": "/api/0/module/data/down_module_day_data",
        "method": "POST",
    }
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_parent(station_id=42, stations=None):
    """Return a minimal MagicMock parent with station and auth context."""
    parent = MagicMock()
    parent.station.station_id = station_id
    parent.station.stations = stations or [{"id": station_id}]
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "solenso_token=tok"}
    return parent


def _make_datamodule(api_response=None) -> MySolensoStationDataModuleDay:
    parent = _make_parent()
    response = api_response if api_response is not None else DATAMODULE_RESPONSE
    with patch("mysolenso.services.stations.datamodule.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = response
        obj = MySolensoStationDataModuleDay(parent)
        obj._get_station_data_module_day()
        return obj


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestMySolensoStationDataModuleDayInit:
    """Construction and validation."""

    def test_raises_when_no_station(self):
        """Constructor raises MySolensoException when station_id is None."""
        parent = _make_parent(station_id=None)
        with pytest.raises(MySolensoException):
            MySolensoStationDataModuleDay(parent)

    def test_stores_station_id(self):
        """Constructor stores the station_id from the parent."""
        parent = _make_parent(station_id=77)
        obj = MySolensoStationDataModuleDay(parent)
        assert obj._station_id == 77

    def test_default_day_is_set(self):
        """A default day in YYYY-MM-DD format is assigned at construction."""
        parent = _make_parent()
        obj = MySolensoStationDataModuleDay(parent)
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", obj._day)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

class TestMySolensoStationDataModuleDayProperties:
    """Property accessors."""

    def test_all_data_returns_first_element(self):
        obj = _make_datamodule()
        assert obj.all_data == DATAMODULE_RESPONSE[0]

    def test_sid(self):
        assert _make_datamodule().sid == 1553580

    def test_url(self):
        assert _make_datamodule().url == "/api/0/module/data/down_module_day_data"

    def test_full_url_contains_base_and_path(self):
        obj = _make_datamodule()
        assert obj.full_url.startswith("https://")
        assert obj.url in obj.full_url

    def test_whitespace_stripped_from_url(self):
        """String fields are stripped of surrounding whitespace."""
        response = [dict(DATAMODULE_RESPONSE[0], url="  /api/0/module/data/down_module_day_data  ")]
        obj = _make_datamodule(api_response=response)
        assert obj.url == "/api/0/module/data/down_module_day_data"


# ---------------------------------------------------------------------------
# set_day
# ---------------------------------------------------------------------------

class TestMySolensoStationDataModuleDaySetDay:
    """set_day validation."""

    def test_set_day_invalid_format_raises(self):
        parent = _make_parent()
        obj = MySolensoStationDataModuleDay(parent)
        with pytest.raises(MySolensoException):
            obj.set_day("2026/05/23", refresh=False)

    def test_set_day_future_raises(self):
        parent = _make_parent()
        obj = MySolensoStationDataModuleDay(parent)
        with pytest.raises(MySolensoException):
            obj.set_day("2999-01-01", refresh=False)

    def test_set_day_valid_stores_day(self):
        parent = _make_parent()
        obj = MySolensoStationDataModuleDay(parent)
        obj.set_day("2025-03-10", refresh=False)
        assert obj._day == "2025-03-10"

    def test_set_day_with_refresh_calls_api(self):
        """set_day with refresh=True triggers a new API call."""
        parent = _make_parent()
        with patch("mysolenso.services.stations.datamodule.MySolensoPost") as MockPost:
            MockPost.return_value.post.return_value = DATAMODULE_RESPONSE
            obj = MySolensoStationDataModuleDay(parent)
            obj._get_station_data_module_day()
            count_before = MockPost.return_value.post.call_count
            obj.set_day("2025-04-01", refresh=True)
            assert MockPost.return_value.post.call_count > count_before


# ---------------------------------------------------------------------------
# set_station
# ---------------------------------------------------------------------------

class TestMySolensoStationDataModuleDaySetStation:
    """set_station behaviour."""

    def test_set_station_invalid_raises(self):
        """set_station raises when the station ID is not in the account list."""
        parent = _make_parent(station_id=42, stations=[{"id": 42}])
        with patch("mysolenso.services.stations.datamodule.MySolensoPost") as MockPost:
            MockPost.return_value.post.return_value = DATAMODULE_RESPONSE
            obj = MySolensoStationDataModuleDay(parent)
            obj._get_station_data_module_day()
            with pytest.raises(MySolensoException):
                obj.set_station(9999, refresh=False)

    def test_set_station_updates_id(self):
        """set_station stores the new station ID."""
        parent = _make_parent(station_id=42, stations=[{"id": 42}, {"id": 43}])
        with patch("mysolenso.services.stations.datamodule.MySolensoPost") as MockPost:
            MockPost.return_value.post.return_value = DATAMODULE_RESPONSE
            obj = MySolensoStationDataModuleDay(parent)
            obj._get_station_data_module_day()
            obj.set_station(43, refresh=False)
            assert obj._station_id == 43

    def test_set_station_with_refresh_calls_api(self):
        """set_station with refresh=True triggers a new API call."""
        parent = _make_parent(station_id=42, stations=[{"id": 42}, {"id": 43}])
        with patch("mysolenso.services.stations.datamodule.MySolensoPost") as MockPost:
            MockPost.return_value.post.return_value = DATAMODULE_RESPONSE
            obj = MySolensoStationDataModuleDay(parent)
            obj._get_station_data_module_day()
            count_before = MockPost.return_value.post.call_count
            obj.set_station(43, refresh=True)
            assert MockPost.return_value.post.call_count > count_before


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestMySolensoStationDataModuleDayErrors:
    """Error handling."""

    def test_empty_response_raises(self):
        parent = _make_parent()
        with patch("mysolenso.services.stations.datamodule.MySolensoPost") as MockPost:
            MockPost.return_value.post.return_value = None
            obj = MySolensoStationDataModuleDay(parent)
            with pytest.raises(MySolensoException):
                obj._get_station_data_module_day()

    def test_network_error_raises(self):
        parent = _make_parent()
        with patch("mysolenso.services.stations.datamodule.MySolensoPost") as MockPost:
            MockPost.return_value.post.side_effect = RuntimeError("connection refused")
            obj = MySolensoStationDataModuleDay(parent)
            with pytest.raises(MySolensoException):
                obj._get_station_data_module_day()

    def test_refresh_calls_api(self):
        parent = _make_parent()
        with patch("mysolenso.services.stations.datamodule.MySolensoPost") as MockPost:
            MockPost.return_value.post.return_value = DATAMODULE_RESPONSE
            obj = MySolensoStationDataModuleDay(parent)
            obj._get_station_data_module_day()
            obj.station_data_module_day_refresh()
            assert MockPost.return_value.post.call_count >= 2

    def test_headers_injected(self):
        """Solenso auth headers are passed to the HTTP client."""
        parent = _make_parent()
        parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "solenso_token=xyz"}
        with patch("mysolenso.services.stations.datamodule.MySolensoPost") as MockPost:
            MockPost.return_value.post.return_value = DATAMODULE_RESPONSE
            obj = MySolensoStationDataModuleDay(parent)
            obj._get_station_data_module_day()
            MockPost.return_value.set_headers.assert_called_with({"Cookie": "solenso_token=xyz"})
