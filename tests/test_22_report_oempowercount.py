"""Tests for MySolensoOEMPowerCount - aggregated OEM PV and consumption totals.

This module covers:
- Construction and default date initialisation.
- Station switching via ``set_station``.
- Date range selection and validation via ``set_day``.
- API response parsing via ``_get_oem_power_count``.
- The ``all_data``, ``total_pv``, and ``total_consumption`` properties.
- The ``oem_power_refresh`` method.
- Error handling for invalid inputs and API failures.
"""

import pytest
from unittest.mock import MagicMock, patch

from mysolenso.services.reports.oempowercount import MySolensoOEMPowerCount
from mysolenso.exceptions import MySolensoException

PATCH_PATH = "mysolenso.services.reports.oempowercount.MySolensoPost"


# ---------------------------------------------------------------------------
# Fixtures / sample data
# ---------------------------------------------------------------------------

SAMPLE_API_RESPONSE = {
    "total_pv_eq": "91.22",
    "total_consumption_eq": "0",
}

SAMPLE_API_RESPONSE_WITH_CONSUMPTION = {
    "total_pv_eq": "250.50",
    "total_consumption_eq": "120.75",
}


def _make_parent(station_id: int = 42, stations: list | None = None) -> MagicMock:
    parent = MagicMock()
    parent.station.station_id = station_id
    parent.station.stations = stations or [{"id": station_id}]
    parent.auth.get_auth_headers_solenso.return_value = {"Authorization": "Bearer tok"}
    return parent


def _make_count(api_response: dict, station_id: int = 42) -> MySolensoOEMPowerCount:
    """Construct MySolensoOEMPowerCount and call _get_oem_power_count."""
    parent = _make_parent(station_id)
    count = MySolensoOEMPowerCount(parent)
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = api_response
        count._get_oem_power_count()
    return count


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_construction_success():
    """MySolensoOEMPowerCount initialises without error when station_id is set."""
    parent = _make_parent()
    count = MySolensoOEMPowerCount(parent)
    assert count is not None


def test_construction_no_station_raises():
    """MySolensoException raised when station_id is None at construction."""
    parent = _make_parent()
    parent.station.station_id = None
    with pytest.raises(MySolensoException, match="station_id is None"):
        MySolensoOEMPowerCount(parent)


def test_construction_default_day_today():
    """Default day_min and day_max are today (hour >= 01:00)."""
    from datetime import datetime
    parent = _make_parent()
    with patch("mysolenso.services.reports.oempowercount.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 5, 15, 10, 0, 0)
        count = MySolensoOEMPowerCount(parent)
    assert count._day_min == "2026-05-22"
    assert count._day_max == "2026-05-22"


def test_construction_midnight_uses_yesterday():
    """Before 01:00, both day_min and day_max default to yesterday."""
    from datetime import datetime
    parent = _make_parent()
    with patch("mysolenso.services.reports.oempowercount.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 5, 15, 0, 30, 0)
        count = MySolensoOEMPowerCount(parent)
    assert count._day_min == "2026-05-14"
    assert count._day_max == "2026-05-14"


# ---------------------------------------------------------------------------
# _get_oem_power_count / all_data
# ---------------------------------------------------------------------------

def test_all_data_returns_dict():
    """all_data returns the raw response dictionary."""
    count = _make_count(SAMPLE_API_RESPONSE)
    assert isinstance(count.all_data, dict)


def test_all_data_values():
    """all_data contains the raw API values."""
    count = _make_count(SAMPLE_API_RESPONSE)
    assert count.all_data["total_pv_eq"] == "91.22"
    assert count.all_data["total_consumption_eq"] == "0"


def test_empty_response_raises():
    """MySolensoException raised when the API returns an empty/falsy body."""
    count = MySolensoOEMPowerCount(_make_parent())
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = None
        with pytest.raises(MySolensoException, match="response data not found"):
            count._get_oem_power_count()


def test_network_error_wrapped():
    """Network-level exceptions are wrapped in MySolensoException."""
    count = MySolensoOEMPowerCount(_make_parent())
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.side_effect = Exception("timeout")
        with pytest.raises(MySolensoException):
            count._get_oem_power_count()


# ---------------------------------------------------------------------------
# total_pv property
# ---------------------------------------------------------------------------

def test_total_pv_value():
    """total_pv returns the cleaned pv_eq string."""
    count = _make_count(SAMPLE_API_RESPONSE)
    assert count.total_pv == "91.22"


def test_total_pv_with_consumption():
    """total_pv works correctly when a consumption value is also present."""
    count = _make_count(SAMPLE_API_RESPONSE_WITH_CONSUMPTION)
    assert count.total_pv == "250.50"


def test_total_pv_none_when_missing():
    """total_pv is None when the field is absent from the API response."""
    count = _make_count({"total_consumption_eq": "0"})
    assert count.total_pv is None


# ---------------------------------------------------------------------------
# total_consumption property
# ---------------------------------------------------------------------------

def test_total_consumption_value():
    """total_consumption returns the cleaned consumption_eq string."""
    count = _make_count(SAMPLE_API_RESPONSE)
    assert count.total_consumption == "0"


def test_total_consumption_with_meter():
    """total_consumption returns the actual value when a meter is installed."""
    count = _make_count(SAMPLE_API_RESPONSE_WITH_CONSUMPTION)
    assert count.total_consumption == "120.75"


def test_total_consumption_none_when_missing():
    """total_consumption is None when the field is absent."""
    count = _make_count({"total_pv_eq": "50.0"})
    assert count.total_consumption is None


# ---------------------------------------------------------------------------
# set_station
# ---------------------------------------------------------------------------

def test_set_station_valid():
    """set_station with a known ID reloads data."""
    count = _make_count(SAMPLE_API_RESPONSE)
    new_id = 99
    count.parent.station.stations = [{"id": 42}, {"id": new_id}]
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = SAMPLE_API_RESPONSE
        count.set_station(new_id)
    assert count._station_id == new_id


def test_set_station_unknown_raises():
    """MySolensoException raised for an unknown station ID."""
    count = _make_count(SAMPLE_API_RESPONSE)
    with pytest.raises(MySolensoException, match="not found"):
        count.set_station(9999)


def test_set_station_no_refresh():
    """set_station(refresh=False) updates station ID without an API call."""
    count = _make_count(SAMPLE_API_RESPONSE)
    count.set_station(42, refresh=False)
    assert count._station_id == 42


# ---------------------------------------------------------------------------
# set_day
# ---------------------------------------------------------------------------

def test_set_day_valid():
    """set_day with a valid range reloads data."""
    count = MySolensoOEMPowerCount(_make_parent())
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = SAMPLE_API_RESPONSE
        count.set_day("2026-04-01", "2026-04-30")
    assert count._day_min == "2026-04-01"
    assert count._day_max == "2026-04-30"


def test_set_day_no_refresh():
    """set_day(refresh=False) updates dates without an API call."""
    count = MySolensoOEMPowerCount(_make_parent())
    count.set_day("2026-04-01", "2026-04-30", refresh=False)
    assert count._day_min == "2026-04-01"
    assert count._day_max == "2026-04-30"


def test_set_day_same_date():
    """set_day accepts day_min == day_max (single-day query)."""
    count = MySolensoOEMPowerCount(_make_parent())
    count.set_day("2026-05-01", "2026-05-01", refresh=False)
    assert count._day_min == count._day_max == "2026-05-01"


def test_set_day_min_after_max_raises():
    """MySolensoException raised when day_min > day_max."""
    count = MySolensoOEMPowerCount(_make_parent())
    with pytest.raises(MySolensoException):
        count.set_day("2026-05-01", "2026-04-01", refresh=False)


def test_set_day_future_raises():
    """MySolensoException raised when a date is in the future."""
    count = MySolensoOEMPowerCount(_make_parent())
    with pytest.raises(MySolensoException):
        count.set_day("2099-01-01", "2099-12-31", refresh=False)


def test_set_day_wrong_format_raises():
    """MySolensoException raised for an invalid date format."""
    count = MySolensoOEMPowerCount(_make_parent())
    with pytest.raises(MySolensoException):
        count.set_day("01/04/2026", "30/04/2026", refresh=False)


def test_set_day_wrong_length_raises():
    """MySolensoException raised when the date string has wrong length."""
    count = MySolensoOEMPowerCount(_make_parent())
    with pytest.raises(MySolensoException):
        count.set_day("2026-4-1", "2026-4-30", refresh=False)


def test_set_day_min_boundary():
    """1900-01-01 is accepted as the minimum date."""
    count = MySolensoOEMPowerCount(_make_parent())
    count.set_day("1900-01-01", "1900-01-01", refresh=False)
    assert count._day_min == "1900-01-01"


def test_set_day_before_min_raises():
    """Date before 1900-01-01 raises MySolensoException."""
    count = MySolensoOEMPowerCount(_make_parent())
    with pytest.raises(MySolensoException):
        count.set_day("1899-12-31", "1900-01-01", refresh=False)


# ---------------------------------------------------------------------------
# oem_power_refresh
# ---------------------------------------------------------------------------

def test_oem_power_refresh_reloads_data():
    """oem_power_refresh triggers a new API call and updates the totals."""
    count = _make_count(SAMPLE_API_RESPONSE)
    updated_response = {"total_pv_eq": "999.99", "total_consumption_eq": "0"}
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = updated_response
        count.oem_power_refresh()
    assert count.total_pv == "999.99"
