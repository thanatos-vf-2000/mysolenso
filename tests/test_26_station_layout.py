"""Tests for MySolensoStationLayout - physical panel placement service."""

import pytest
from unittest.mock import MagicMock, patch

from mysolenso.services.stations.layout import MySolensoStationLayout
from mysolenso.exceptions import MySolensoException


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

LAYOUT_RESPONSE = [
    {
        "id": 8967073,
        "aid": 268104,
        "dtu_id": 1456060,
        "dtu_sn": "D0100289H",
        "dev_type": 3,
        "mi_id": 6654220,
        "mi_sn": "A110016B1",
        "port": 1,
        "x": 0,
        "y": 0,
    },
    {
        "id": 8967074,
        "aid": 268104,
        "dtu_id": 1456060,
        "dtu_sn": "D0100289H",
        "dev_type": 3,
        "mi_id": 6654220,
        "mi_sn": "A110016B1",
        "port": 2,
        "x": 0,
        "y": 1,
    },
    {
        "id": 8967075,
        "aid": 268104,
        "dtu_id": 1456060,
        "dtu_sn": "D0100289H",
        "dev_type": 3,
        "mi_id": 6654230,
        "mi_sn": "A110016GV",
        "port": 1,
        "x": 0,
        "y": 2,
    },
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


def _make_layout(api_response=None) -> MySolensoStationLayout:
    parent = _make_parent()
    response = api_response if api_response is not None else LAYOUT_RESPONSE
    with patch("mysolenso.services.stations.layout.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = response
        obj = MySolensoStationLayout(parent)
        obj._get_station_layout()
        return obj


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestMySolensoStationLayoutInit:
    """Construction and validation."""

    def test_raises_when_no_station(self):
        """Constructor raises MySolensoException when station_id is None."""
        parent = _make_parent(station_id=None)
        with pytest.raises(MySolensoException):
            MySolensoStationLayout(parent)

    def test_stores_station_id(self):
        """Constructor stores the station_id from the parent."""
        parent = _make_parent(station_id=99)
        obj = MySolensoStationLayout(parent)
        assert obj._station_id == 99


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

class TestMySolensoStationLayoutProperties:
    """Property accessors."""

    def test_all_data_returns_raw_list(self):
        obj = _make_layout()
        assert obj.all_data == LAYOUT_RESPONSE

    def test_list_dtu_deduplicates(self):
        """list_dtu returns one entry per unique DTU id."""
        obj = _make_layout()
        dtus = obj.list_dtu
        assert len(dtus) == 1
        assert dtus[0]["dtu_id"] == 1456060
        assert dtus[0]["dtu_sn"] == "D0100289H"

    def test_list_dtu_ids_returns_unique_ids(self):
        obj = _make_layout()
        ids = obj.list_dtu_ids()
        assert ids == [1456060]

    def test_list_dtu_raises_when_empty(self):
        """list_dtu raises ValueError when _all_data is empty."""
        obj = _make_layout()
        obj._all_data = []
        with pytest.raises(ValueError):
            _ = obj.list_dtu

    def test_get_mi_info_by_dtu_returns_sorted_list(self):
        """get_mi_info_by_dtu returns panels sorted by (x, y)."""
        obj = _make_layout()
        panels = obj.get_mi_info_by_dtu(dtu_id=1456060)
        assert len(panels) == 3
        ys = [p["y"] for p in panels]
        assert ys == sorted(ys)

    def test_get_mi_info_by_dtu_panel_keys(self):
        """Each panel record contains the expected keys."""
        obj = _make_layout()
        panel = obj.get_mi_info_by_dtu(dtu_id=1456060)[0]
        assert set(panel.keys()) == {"id", "sn", "port", "x", "y"}

    def test_get_mi_info_by_dtu_unknown_id_returns_empty(self):
        """get_mi_info_by_dtu returns an empty list for an unknown DTU id."""
        obj = _make_layout()
        assert obj.get_mi_info_by_dtu(dtu_id=9999999) == []


# ---------------------------------------------------------------------------
# set_station
# ---------------------------------------------------------------------------

class TestMySolensoStationLayoutSetStation:
    """set_station behaviour."""

    def test_set_station_invalid_raises(self):
        parent = _make_parent(station_id=42, stations=[{"id": 42}])
        with patch("mysolenso.services.stations.layout.MySolensoPost") as MockPost:
            MockPost.return_value.post.return_value = LAYOUT_RESPONSE
            obj = MySolensoStationLayout(parent)
            obj._get_station_layout()
            with pytest.raises(MySolensoException):
                obj.set_station(999, refresh=False)

    def test_set_station_updates_id(self):
        parent = _make_parent(station_id=42, stations=[{"id": 42}, {"id": 43}])
        with patch("mysolenso.services.stations.layout.MySolensoPost") as MockPost:
            MockPost.return_value.post.return_value = LAYOUT_RESPONSE
            obj = MySolensoStationLayout(parent)
            obj._get_station_layout()
            obj.set_station(43, refresh=False)
            assert obj._station_id == 43

    def test_set_station_with_refresh_calls_api(self):
        parent = _make_parent(station_id=42, stations=[{"id": 42}, {"id": 43}])
        with patch("mysolenso.services.stations.layout.MySolensoPost") as MockPost:
            MockPost.return_value.post.return_value = LAYOUT_RESPONSE
            obj = MySolensoStationLayout(parent)
            obj._get_station_layout()
            count_before = MockPost.return_value.post.call_count
            obj.set_station(43, refresh=True)
            assert MockPost.return_value.post.call_count > count_before


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestMySolensoStationLayoutErrors:
    """Error handling."""

    def test_empty_response_raises(self):
        parent = _make_parent()
        with patch("mysolenso.services.stations.layout.MySolensoPost") as MockPost:
            MockPost.return_value.post.return_value = None
            obj = MySolensoStationLayout(parent)
            with pytest.raises(MySolensoException):
                obj._get_station_layout()

    def test_network_error_raises(self):
        parent = _make_parent()
        with patch("mysolenso.services.stations.layout.MySolensoPost") as MockPost:
            MockPost.return_value.post.side_effect = Exception("timeout")
            obj = MySolensoStationLayout(parent)
            with pytest.raises(MySolensoException):
                obj._get_station_layout()

    def test_refresh_calls_api(self):
        parent = _make_parent()
        with patch("mysolenso.services.stations.layout.MySolensoPost") as MockPost:
            MockPost.return_value.post.return_value = LAYOUT_RESPONSE
            obj = MySolensoStationLayout(parent)
            obj._get_station_layout()
            obj.station_layout_refresh()
            assert MockPost.return_value.post.call_count >= 2
