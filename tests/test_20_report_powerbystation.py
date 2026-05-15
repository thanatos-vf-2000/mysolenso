"""Tests for MySolensoPowerByStation — per-station daily power aggregation."""
 
import pytest
from unittest.mock import MagicMock, patch
 
from mysolenso.services.reports.powerbystation import MySolensoPowerByStation
from mysolenso.exceptions import MySolensoException
 
# Correct patch path — module lives under services.reports, not services
PATCH_PATH = "mysolenso.services.reports.powerbystation.MySolensoPost"
 
 
# ---------------------------------------------------------------------------
# Fixtures / sample data
# ---------------------------------------------------------------------------
 
STATION_DETAIL = {
    "sid": 9876543,
    "name": "DOE JOHN",
    "tz_name": "UTC+01",
    "is_reflux": 0,
    "is_balance": 0,
    "meter_location": 0,
    "classify": 1,
    "dw": None,
    "data_list": [
        {
            "date": "06:15",
            "pv_power": "26",
            "consumption_power": "0",
            "meter_c_power": "0",
            "grid_p_power": "0",
            "bms_power": "0",
            "meter_location": 0,
        },
        {
            "date": "06:30",
            "pv_power": "56",
            "consumption_power": "0",
            "meter_c_power": "0",
            "grid_p_power": "0",
            "bms_power": "0",
            "meter_location": 0,
        },
        {
            "date": "17:30",
            "pv_power": "1449",
            "consumption_power": "0",
            "meter_c_power": "0",
            "grid_p_power": "0",
            "bms_power": "0",
            "meter_location": 0,
        },
        {
            "date": "17:45",
            "pv_power": "1523",
            "consumption_power": "0",
            "meter_c_power": "0",
            "grid_p_power": "0",
            "bms_power": "0",
            "meter_location": 0,
        },
        {
            "date": "22:00",
            "pv_power": "0",
            "consumption_power": "0",
            "meter_c_power": "0",
            "grid_p_power": "0",
            "bms_power": "0",
            "meter_location": 0,
        },
        {
            "date": "22:15",
            "pv_power": "0",
            "consumption_power": "0",
            "meter_c_power": "0",
            "grid_p_power": "0",
            "bms_power": "0",
            "meter_location": 0,
        },
    ],
}
 
 
def _make_parent(station_id: int = 42, extra_stations: list = None):
    """Build a mock parent with a configured station sub-module."""
    parent = MagicMock()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "tok"}
    parent.station.station_id = station_id
    stations = [{"id": station_id, "ak": "ak_abc"}]
    if extra_stations:
        stations.extend(extra_stations)
    parent.station.stations = stations
    return parent
 
 
def _make_powerbystation(
    api_data: dict | list,
    station_id: int = 42,
) -> MySolensoPowerByStation:
    """
    Instantiate MySolensoPowerByStation with a mocked POST.
 
    The API returns a list; _get_power_by_station takes response[0].
    Pass api_data as a dict (one record) — the helper wraps it in a list.
    """
    parent = _make_parent(station_id)
    with patch(PATCH_PATH) as MockPost:
        # API returns a list; the service takes [0]
        MockPost.return_value.post.return_value = [api_data]
        sd = MySolensoPowerByStation(parent)
        # Trigger initial fetch (not called in __init__)
        sd.get_power_station_refresh()
    return sd
 
 
# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------
 
def test_none_station_id_raises():
    """station_id=None on parent raises MySolensoException."""
    parent = MagicMock()
    parent.station.station_id = None
    with pytest.raises(MySolensoException):
        MySolensoPowerByStation(parent)
 
 
def test_construction_does_not_fetch():
    """__init__ must not make any network call (no auto-fetch)."""
    parent = _make_parent()
    with patch(PATCH_PATH) as MockPost:
        MySolensoPowerByStation(parent)
        MockPost.return_value.post.assert_not_called()
 
 
# ---------------------------------------------------------------------------
# all_data — requires explicit refresh call first
# ---------------------------------------------------------------------------
 
def test_all_data_raises_before_refresh():
    """Accessing all_data before any fetch raises AttributeError."""
    parent = _make_parent()
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = [STATION_DETAIL]
        sd = MySolensoPowerByStation(parent)
    # _all_data not set yet
    with pytest.raises(AttributeError):
        _ = sd.all_data
 
 
def test_all_data_after_refresh():
    """all_data returns the first element of the API response list."""
    sd = _make_powerbystation(STATION_DETAIL)
    assert sd.all_data == STATION_DETAIL
 
 
def test_all_data_sid():
    sd = _make_powerbystation(STATION_DETAIL)
    assert sd.all_data["sid"] == 9876543
 
 
def test_all_data_name():
    sd = _make_powerbystation(STATION_DETAIL)
    assert sd.all_data["name"] == "DOE JOHN"
 
 
def test_all_data_tz_name():
    sd = _make_powerbystation(STATION_DETAIL)
    assert sd.all_data["tz_name"] == "UTC+01"
 
 
def test_all_data_contains_data_list():
    sd = _make_powerbystation(STATION_DETAIL)
    assert "data_list" in sd.all_data
    assert len(sd.all_data["data_list"]) == 6
 
 
# ---------------------------------------------------------------------------
# get_power_station_refresh
# ---------------------------------------------------------------------------
 
def test_refresh_reloads_data():
    """get_power_station_refresh updates all_data with the new API response."""
    parent = _make_parent()
    updated = {**STATION_DETAIL, "name": "UPDATED NAME"}
 
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = [STATION_DETAIL]
        sd = MySolensoPowerByStation(parent)
        sd.get_power_station_refresh()
        assert sd.all_data["name"] == "DOE JOHN"
 
        # Simulate API returning new data
        MockPost.return_value.post.return_value = [updated]
        sd.get_power_station_refresh()
 
    assert sd.all_data["name"] == "UPDATED NAME"
 
 
def test_refresh_empty_response_raises():
    """Empty API response list raises MySolensoException."""
    parent = _make_parent()
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = [STATION_DETAIL]
        sd = MySolensoPowerByStation(parent)
        sd.get_power_station_refresh()
 
        MockPost.return_value.post.return_value = []
        with pytest.raises(MySolensoException):
            sd.get_power_station_refresh()
 
 
def test_refresh_network_error_raises():
    """Network error during refresh raises MySolensoException."""
    parent = _make_parent()
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = [STATION_DETAIL]
        sd = MySolensoPowerByStation(parent)
        sd.get_power_station_refresh()
 
        MockPost.return_value.post.side_effect = Exception("timeout")
        with pytest.raises(MySolensoException):
            sd.get_power_station_refresh()
 
 
# ---------------------------------------------------------------------------
# set_station
# ---------------------------------------------------------------------------
 
def test_set_station_valid():
    """set_station switches station and reloads data."""
    parent = _make_parent(station_id=42, extra_stations=[{"id": 43, "ak": "b"}])
    updated = {**STATION_DETAIL, "name": "STATION 43"}
 
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = [STATION_DETAIL]
        sd = MySolensoPowerByStation(parent)
        sd.get_power_station_refresh()
 
        MockPost.return_value.post.return_value = [updated]
        sd.set_station(43)
 
    assert sd._station_id == 43
    assert sd.all_data["name"] == "STATION 43"
 
 
def test_set_station_no_refresh():
    """set_station with refresh=False does not call the API."""
    parent = _make_parent(station_id=42, extra_stations=[{"id": 43, "ak": "b"}])
 
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = [STATION_DETAIL]
        sd = MySolensoPowerByStation(parent)
        sd.get_power_station_refresh()
        call_count = MockPost.return_value.post.call_count
 
        sd.set_station(43, refresh=False)
 
    assert sd._station_id == 43
    assert MockPost.return_value.post.call_count == call_count  # no extra call
 
 
def test_set_station_invalid_raises():
    """set_station with unknown ID raises MySolensoException."""
    sd = _make_powerbystation(STATION_DETAIL)
    with pytest.raises(MySolensoException):
        sd.set_station(999)
 
 
# ---------------------------------------------------------------------------
# set_day
# ---------------------------------------------------------------------------
 
def test_set_day_valid():
    """set_day stores the date and triggers a reload."""
    parent = _make_parent()
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = [STATION_DETAIL]
        sd = MySolensoPowerByStation(parent)
        sd.get_power_station_refresh()
        sd.set_day("2025-07-14")
 
    assert sd._day == "2025-07-14"
 
 
def test_set_day_no_refresh():
    """set_day with refresh=False stores date without API call."""
    parent = _make_parent()
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = [STATION_DETAIL]
        sd = MySolensoPowerByStation(parent)
        sd.get_power_station_refresh()
        call_count = MockPost.return_value.post.call_count
 
        sd.set_day("2025-01-01", refresh=False)
 
    assert sd._day == "2025-01-01"
    assert MockPost.return_value.post.call_count == call_count
 
 
def test_set_day_invalid_format_raises():
    """Non-YYYY-MM-DD format raises MySolensoException."""
    sd = _make_powerbystation(STATION_DETAIL)
    with pytest.raises(MySolensoException):
        sd.set_day("14/07/2025")
 
 
def test_set_day_wrong_length_raises():
    """Date string with wrong length raises MySolensoException."""
    sd = _make_powerbystation(STATION_DETAIL)
    with pytest.raises(MySolensoException):
        sd.set_day("2025-7-4")
 
 
def test_set_day_future_raises():
    """Future date raises MySolensoException."""
    sd = _make_powerbystation(STATION_DETAIL)
    with pytest.raises(MySolensoException):
        sd.set_day("2099-01-01")
 
 
def test_set_day_min_boundary():
    """1900-01-01 is the minimum accepted date."""
    parent = _make_parent()
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = [STATION_DETAIL]
        sd = MySolensoPowerByStation(parent)
        sd.get_power_station_refresh()
        sd.set_day("1900-01-01", refresh=False)
 
    assert sd._day == "1900-01-01"
 
 
def test_set_day_before_min_raises():
    """Date before 1900-01-01 raises MySolensoException."""
    sd = _make_powerbystation(STATION_DETAIL)
    with pytest.raises(MySolensoException):
        sd.set_day("1899-12-31")
 
 
# ---------------------------------------------------------------------------
# extract_power_data
# ---------------------------------------------------------------------------
 
def test_extract_power_data_values():
    """extract_power_data returns correct date/power pairs."""
    sd = _make_powerbystation(STATION_DETAIL)
    result = sd.extract_power_data
 
    assert result[0] == {"date": "06:15", "power": 26}
    assert result[1] == {"date": "06:30", "power": 56}
    assert result[2] == {"date": "17:30", "power": 1449}
    assert result[3] == {"date": "17:45", "power": 1523}
 
 
def test_extract_power_data_zeros():
    """Zero pv_power values are included in the result."""
    sd = _make_powerbystation(STATION_DETAIL)
    result = sd.extract_power_data
 
    assert result[4] == {"date": "22:00", "power": 0}
    assert result[5] == {"date": "22:15", "power": 0}
 
 
def test_extract_power_data_length():
    """Result contains the same number of entries as data_list."""
    sd = _make_powerbystation(STATION_DETAIL)
    assert len(sd.extract_power_data) == len(STATION_DETAIL["data_list"])
 
 
def test_extract_power_data_types():
    """power values are int, not str."""
    sd = _make_powerbystation(STATION_DETAIL)
    for item in sd.extract_power_data:
        assert isinstance(item["power"], int)
        assert isinstance(item["date"], str)
 
 
def test_extract_power_data_missing_data_list_raises():
    """Missing data_list raises ValueError."""
    sd = _make_powerbystation({**STATION_DETAIL, "data_list": None})
    with pytest.raises(ValueError):
        sd.extract_power_data
 
 
def test_extract_power_data_empty_data_list_raises():
    """Empty data_list raises ValueError."""
    sd = _make_powerbystation({**STATION_DETAIL, "data_list": []})
    with pytest.raises(ValueError):
        sd.extract_power_data
 
 
# ---------------------------------------------------------------------------
# API error handling (construction-time fetch via refresh)
# ---------------------------------------------------------------------------
 
def test_api_error_on_refresh_raises():
    """Network error during refresh raises MySolensoException."""
    parent = _make_parent()
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.side_effect = Exception("timeout")
        sd = MySolensoPowerByStation(parent)
        with pytest.raises(MySolensoException):
            sd.get_power_station_refresh()