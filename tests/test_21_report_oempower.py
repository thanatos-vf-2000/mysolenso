"""Tests for MySolensoOEMPower - OEM daily PV energy list report.

This module covers:
- Construction and default date initialisation.
- Station switching via ``set_station``.
- Date range selection and validation via ``set_day``.
- API response parsing via ``_get_oem_pv``.
- The ``all_data`` and ``power_data`` properties.
- The ``oem_pv_refresh`` method.
- Error handling for invalid inputs and API failures.
"""

import pytest
from unittest.mock import MagicMock, patch

from mysolenso.services.reports.oempower import MySolensoOEMPower
from mysolenso.exceptions import MySolensoException

PATCH_PATH = "mysolenso.services.reports.oempower.MySolensoPost"


# ---------------------------------------------------------------------------
# Fixtures / sample data
# ---------------------------------------------------------------------------

SAMPLE_RECORDS = [
    {
        "sid": 9876543,
        "name": "DOE JOHN",
        "tz_name": "Africa/Windhoek",
        "date": "2026-04-11",
        "pv_eq": "14.58",
        "consumption_eq": "-",
        "meter_c_eq": "0",
        "meter_location": 0,
        "capacitor": 0,
        "create_at": None,
        "p2g": None,
        "lfg": None,
        "eq_hour": 0,
    },
    {
        "sid": 9876543,
        "name": "DOE JOHN",
        "tz_name": "Africa/Windhoek",
        "date": "2026-04-12",
        "pv_eq": "25.2",
        "consumption_eq": "-",
        "meter_c_eq": "0",
        "meter_location": 0,
        "capacitor": 0,
        "create_at": None,
        "p2g": None,
        "lfg": None,
        "eq_hour": 0,
    },
]

SAMPLE_API_RESPONSE = {"list": SAMPLE_RECORDS, "total": 2}


def _make_parent(station_id: int = 42, stations: list | None = None) -> MagicMock:
    parent = MagicMock()
    parent.station.station_id = station_id
    parent.station.stations = stations or [{"id": station_id}]
    parent.auth.get_auth_headers_solenso.return_value = {"Authorization": "Bearer tok"}
    return parent


def _make_oem(api_response: dict, station_id: int = 42) -> MySolensoOEMPower:
    """Construct MySolensoOEMPower and call _get_oem_pv with a mocked response."""
    parent = _make_parent(station_id)
    oem = MySolensoOEMPower(parent)
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = api_response
        oem._get_oem_pv()
    return oem


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_construction_success():
    """MySolensoOEMPower initialises without error when station_id is set."""
    parent = _make_parent()
    oem = MySolensoOEMPower(parent)
    assert oem is not None


def test_construction_no_station_raises():
    """MySolensoException raised when station_id is None at construction."""
    parent = _make_parent()
    parent.station.station_id = None
    with pytest.raises(MySolensoException, match="station_id is None"):
        MySolensoOEMPower(parent)


def test_construction_default_day_range_today():
    """Default day_min and day_max are both set to today (hour >= 01:00)."""
    from datetime import datetime
    parent = _make_parent()
    with patch("mysolenso.services.reports.oempower.datetime") as mock_dt:
        fake_now = datetime(2026, 5, 22, 10, 0, 0)
        mock_dt.now.return_value = fake_now
        oem = MySolensoOEMPower(parent)
    assert oem._day_min == "2026-05-22"
    assert oem._day_max == "2026-05-22"


def test_construction_midnight_uses_yesterday():
    """Before 01:00, both day_min and day_max default to yesterday."""
    from datetime import datetime
    parent = _make_parent()
    with patch("mysolenso.services.reports.oempower.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 5, 15, 0, 30, 0)
        oem = MySolensoOEMPower(parent)
    assert oem._day_min == "2026-05-14"
    assert oem._day_max == "2026-05-14"


# ---------------------------------------------------------------------------
# _get_oem_pv / all_data
# ---------------------------------------------------------------------------

def test_all_data_returns_list():
    """all_data returns the list of records from the API response."""
    oem = _make_oem(SAMPLE_API_RESPONSE)
    assert isinstance(oem.all_data, list)
    assert len(oem.all_data) == 2


def test_all_data_record_fields():
    """Each record in all_data contains the expected keys."""
    oem = _make_oem(SAMPLE_API_RESPONSE)
    for record in oem.all_data:
        assert "date" in record
        assert "pv_eq" in record
        assert "sid" in record


def test_all_data_values_match_sample():
    """all_data records match the mocked API payload."""
    oem = _make_oem(SAMPLE_API_RESPONSE)
    assert oem.all_data[0]["date"] == "2026-04-11"
    assert oem.all_data[0]["pv_eq"] == "14.58"
    assert oem.all_data[1]["date"] == "2026-04-12"
    assert oem.all_data[1]["pv_eq"] == "25.2"


def test_empty_response_raises():
    """MySolensoException raised when the API returns an empty/falsy body."""
    oem = MySolensoOEMPower(_make_parent())
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = None
        with pytest.raises(MySolensoException, match="response data not found"):
            oem._get_oem_pv()


def test_zero_total_raises():
    """MySolensoException raised when total is 0 (no records)."""
    oem = MySolensoOEMPower(_make_parent())
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = {"list": [], "total": 0}
        with pytest.raises(MySolensoException, match="no data"):
            oem._get_oem_pv()


def test_network_error_wrapped():
    """Network-level exceptions are wrapped in MySolensoException."""
    oem = MySolensoOEMPower(_make_parent())
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.side_effect = Exception("connection error")
        with pytest.raises(MySolensoException):
            oem._get_oem_pv()


# ---------------------------------------------------------------------------
# power_data property
# ---------------------------------------------------------------------------

def test_power_data_structure():
    """power_data returns a list of {date, power} dicts."""
    oem = _make_oem(SAMPLE_API_RESPONSE)
    result = oem.power_data
    assert isinstance(result, list)
    for item in result:
        assert "date" in item
        assert "power" in item


def test_power_data_values():
    """power_data entries match the pv_eq and date fields."""
    oem = _make_oem(SAMPLE_API_RESPONSE)
    result = oem.power_data
    assert result[0] == {"date": "2026-04-11", "power": "14.58"}
    assert result[1] == {"date": "2026-04-12", "power": "25.2"}


def test_power_data_length():
    """power_data length equals the number of records in all_data."""
    oem = _make_oem(SAMPLE_API_RESPONSE)
    assert len(oem.power_data) == len(oem.all_data)


def test_power_data_empty_all_data_raises():
    """ValueError raised when all_data is empty."""
    oem = MySolensoOEMPower(_make_parent())
    oem._all_data = []
    with pytest.raises(ValueError, match="empty"):
        _ = oem.power_data


# ---------------------------------------------------------------------------
# set_station
# ---------------------------------------------------------------------------

def test_set_station_valid():
    """set_station with a known ID reloads data."""
    oem = _make_oem(SAMPLE_API_RESPONSE)
    new_id = 99
    oem.parent.station.stations = [{"id": 42}, {"id": new_id}]
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = SAMPLE_API_RESPONSE
        oem.set_station(new_id)
    assert oem._station_id == new_id


def test_set_station_unknown_raises():
    """MySolensoException raised for an unknown station ID."""
    oem = _make_oem(SAMPLE_API_RESPONSE)
    with pytest.raises(MySolensoException, match="not found"):
        oem.set_station(9999)


def test_set_station_no_refresh():
    """set_station(refresh=False) updates station ID without an API call."""
    oem = _make_oem(SAMPLE_API_RESPONSE)
    oem.set_station(42, refresh=False)
    assert oem._station_id == 42


# ---------------------------------------------------------------------------
# set_day
# ---------------------------------------------------------------------------

def test_set_day_valid():
    """set_day with a valid range reloads data."""
    oem = MySolensoOEMPower(_make_parent())
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = SAMPLE_API_RESPONSE
        oem.set_day("2026-04-01", "2026-04-30")
    assert oem._day_min == "2026-04-01"
    assert oem._day_max == "2026-04-30"


def test_set_day_no_refresh():
    """set_day(refresh=False) updates dates without an API call."""
    oem = MySolensoOEMPower(_make_parent())
    oem.set_day("2026-04-01", "2026-04-30", refresh=False)
    assert oem._day_min == "2026-04-01"
    assert oem._day_max == "2026-04-30"


def test_set_day_same_date():
    """set_day accepts day_min == day_max (single-day range)."""
    oem = MySolensoOEMPower(_make_parent())
    oem.set_day("2026-05-01", "2026-05-01", refresh=False)
    assert oem._day_min == oem._day_max == "2026-05-01"


def test_set_day_min_after_max_raises():
    """MySolensoException raised when day_min > day_max."""
    oem = MySolensoOEMPower(_make_parent())
    with pytest.raises(MySolensoException):
        oem.set_day("2026-05-01", "2026-04-01", refresh=False)


def test_set_day_future_raises():
    """MySolensoException raised when a date is in the future."""
    oem = MySolensoOEMPower(_make_parent())
    with pytest.raises(MySolensoException):
        oem.set_day("2099-01-01", "2099-12-31", refresh=False)


def test_set_day_wrong_format_raises():
    """MySolensoException raised for invalid date format."""
    oem = MySolensoOEMPower(_make_parent())
    with pytest.raises(MySolensoException):
        oem.set_day("01/04/2026", "30/04/2026", refresh=False)


def test_set_day_wrong_length_raises():
    """MySolensoException raised when the date string has wrong length."""
    oem = MySolensoOEMPower(_make_parent())
    with pytest.raises(MySolensoException):
        oem.set_day("2026-4-1", "2026-4-30", refresh=False)


# ---------------------------------------------------------------------------
# oem_pv_refresh
# ---------------------------------------------------------------------------

def test_oem_pv_refresh_reloads_data():
    """oem_pv_refresh triggers a new API call and updates all_data."""
    oem = _make_oem(SAMPLE_API_RESPONSE)
    new_record = [{**SAMPLE_RECORDS[0], "pv_eq": "99.99"}]
    new_response = {"list": new_record, "total": 1}
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.post.return_value = new_response
        oem.oem_pv_refresh()
    assert oem.all_data[0]["pv_eq"] == "99.99"
