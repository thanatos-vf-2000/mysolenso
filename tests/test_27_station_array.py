"""Tests for MySolensoStationArray - solar panel array configuration service."""

import pytest
from unittest.mock import MagicMock, patch

from mysolenso.services.stations.array import MySolensoStationArray
from mysolenso.exceptions import MySolensoException


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

ARRAY_RESPONSE = [
    {
        "id": 268104,
        "name": "DOE JOHN",
        "angle_tilt": 20,
        "orientation": 0,
        "row": 0,
        "column": 9,
        "pattern": 1,
        "layout_tilt": 0,
        "e_min_x": 0,
        "e_min_y": 0,
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


def _make_array(api_response=None) -> MySolensoStationArray:
    parent = _make_parent()
    response = api_response if api_response is not None else ARRAY_RESPONSE
    with patch("mysolenso.services.stations.array.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = response
        obj = MySolensoStationArray(parent)
        obj._get_station_array()
        return obj


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestMySolensoStationArrayInit:
    """Construction and validation."""

    def test_raises_when_no_station(self):
        """Constructor raises MySolensoException when station_id is None."""
        parent = _make_parent(station_id=None)
        with pytest.raises(MySolensoException):
            MySolensoStationArray(parent)

    def test_stores_station_id(self):
        """Constructor stores the station_id from the parent."""
        parent = _make_parent(station_id=7)
        obj = MySolensoStationArray(parent)
        assert obj._station_id == 7


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

class TestMySolensoStationArrayProperties:
    """Property accessors."""

    def test_all_data_returns_first_element(self):
        obj = _make_array()
        assert obj.all_data == ARRAY_RESPONSE[0]

    def test_id(self):
        assert _make_array().id == 268104

    def test_name(self):
        assert _make_array().name == "DOE JOHN"

    def test_angle_tilt(self):
        assert _make_array().angle_tilt == 20

    def test_orientation(self):
        assert _make_array().orientation == 0

    def test_row(self):
        assert _make_array().row == 0

    def test_column(self):
        assert _make_array().column == 9

    def test_layout_tilt(self):
        assert _make_array().layout_tilt == 0

    def test_e_min_x(self):
        assert _make_array().e_min_x == 0

    def test_e_min_y(self):
        assert _make_array().e_min_y == 0

    def test_whitespace_stripped_from_name(self):
        """String fields are stripped of surrounding whitespace."""
        response = [dict(ARRAY_RESPONSE[0], name="  PADDED NAME  ")]
        obj = _make_array(api_response=response)
        assert obj.name == "PADDED NAME"


# ---------------------------------------------------------------------------
# set_station
# ---------------------------------------------------------------------------

class TestMySolensoStationArraySetStation:
    """set_station behaviour."""

    def test_set_station_invalid_raises(self):
        """set_station raises when the station ID is not in the account list."""
        parent = _make_parent(station_id=42, stations=[{"id": 42}])
        with patch("mysolenso.services.stations.array.MySolensoPost") as MockPost:
            MockPost.return_value.post.return_value = ARRAY_RESPONSE
            obj = MySolensoStationArray(parent)
            obj._get_station_array()
            with pytest.raises(MySolensoException):
                obj.set_station(999, refresh=False)

    def test_set_station_updates_id(self):
        """set_station stores the new station ID."""
        parent = _make_parent(station_id=42, stations=[{"id": 42}, {"id": 43}])
        with patch("mysolenso.services.stations.array.MySolensoPost") as MockPost:
            MockPost.return_value.post.return_value = ARRAY_RESPONSE
            obj = MySolensoStationArray(parent)
            obj._get_station_array()
            obj.set_station(43, refresh=False)
            assert obj._station_id == 43

    def test_set_station_with_refresh_calls_api(self):
        """set_station with refresh=True triggers a new API call."""
        parent = _make_parent(station_id=42, stations=[{"id": 42}, {"id": 43}])
        with patch("mysolenso.services.stations.array.MySolensoPost") as MockPost:
            MockPost.return_value.post.return_value = ARRAY_RESPONSE
            obj = MySolensoStationArray(parent)
            obj._get_station_array()
            count_before = MockPost.return_value.post.call_count
            obj.set_station(43, refresh=True)
            assert MockPost.return_value.post.call_count > count_before


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestMySolensoStationArrayErrors:
    """Error handling."""

    def test_empty_response_raises(self):
        parent = _make_parent()
        with patch("mysolenso.services.stations.array.MySolensoPost") as MockPost:
            MockPost.return_value.post.return_value = None
            obj = MySolensoStationArray(parent)
            with pytest.raises(MySolensoException):
                obj._get_station_array()

    def test_network_error_raises(self):
        parent = _make_parent()
        with patch("mysolenso.services.stations.array.MySolensoPost") as MockPost:
            MockPost.return_value.post.side_effect = RuntimeError("network down")
            obj = MySolensoStationArray(parent)
            with pytest.raises(MySolensoException):
                obj._get_station_array()

    def test_refresh_calls_api(self):
        parent = _make_parent()
        with patch("mysolenso.services.stations.array.MySolensoPost") as MockPost:
            MockPost.return_value.post.return_value = ARRAY_RESPONSE
            obj = MySolensoStationArray(parent)
            obj._get_station_array()
            obj.station_array_refresh()
            assert MockPost.return_value.post.call_count >= 2
