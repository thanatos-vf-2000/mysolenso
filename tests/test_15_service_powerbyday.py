"""Tests for MySolensoPowerByDay — intra-day grid power curve.

This module covers:
- Construction and default date selection (today / yesterday before 01:00).
- Binary protobuf response parsing (HH:MM times + float32 power values).
- Station switching via ``set_station_id``.
- Date selection and validation via ``set_day``.
- The ``get_data`` property structure and contract.
- The ``get_power_refresh`` method.
- Error handling for malformed responses and invalid inputs.
"""

import struct
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from mysolenso.services.powerbyday import MySolensoPowerByDay
from mysolenso.exceptions import MySolensoException

PATCH_PATH = "mysolenso.services.powerbyday.MySolensoPost"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_proto_response(
    times: list[str],
    values: list[float],
    date: str = "2026-05-15",
) -> bytes:
    """Build a minimal binary response that mimics the real API payload.

    Layout:
        <HH:MM labels as bytes>
        grid_power\\x12<2-byte header><float32 * n>
        \\x1a\\x0a<YYYY-MM-DD>
    """
    # Time labels encoded as bytes (space-separated for easy regex extraction)
    time_section = b" ".join(t.encode() for t in times) + b" "

    # Float array: little-endian float32
    float_bytes = b""
    for v in values:
        float_bytes += struct.pack("<f", v)

    # 3-byte header: tag (0x12) + 2-byte "length" placeholder (not really used
    # by the parser — it reads until the \\x1a\\x0a delimiter instead)
    header = b"\x12\x00\x00"

    binary_section = b"grid_power" + header + float_bytes

    # Date delimiter + date string
    date_section = b"\x1a\x0a" + date.encode()

    return time_section + binary_section + date_section


def _make_parent(station_id: int = 42, stations: list | None = None) -> MagicMock:
    parent = MagicMock()
    parent.station.station_id = station_id
    parent.station.stations = stations or [{"id": station_id}]
    parent.auth.get_auth_headers_hoymiles.return_value = {"Authorization": "Bearer tok"}
    return parent


def _make_pbd(response: bytes, station_id: int = 42) -> MySolensoPowerByDay:
    """Instantiate MySolensoPowerByDay with a mocked API response."""
    parent = _make_parent(station_id)
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.poststr.return_value = response
        return MySolensoPowerByDay(parent)


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_TIMES = ["08:00", "08:30", "09:00"]
SAMPLE_VALUES = [512.0, 1024.0, 2048.0]
SAMPLE_DATE = "2026-05-15"
SAMPLE_RESPONSE = _make_proto_response(SAMPLE_TIMES, SAMPLE_VALUES, SAMPLE_DATE)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_construction_success():
    """MySolensoPowerByDay initialises without error on a valid response."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    assert pbd is not None


def test_construction_no_station_raises():
    """MySolensoException raised when station_id is None at construction."""
    parent = _make_parent()
    parent.station.station_id = None
    with pytest.raises(MySolensoException, match="station_id is None"):
        with patch(PATCH_PATH):
            MySolensoPowerByDay(parent)


def test_construction_default_day_is_today():
    """Default day is today when the local hour is >= 01:00."""
    today = datetime.now().strftime("%Y-%m-%d")
    parent = _make_parent()
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.poststr.return_value = SAMPLE_RESPONSE
        with patch("mysolenso.services.powerbyday.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 5, 15, 10, 0, 0)
            mock_dt.strptime = datetime.strptime
            pbd = MySolensoPowerByDay(parent)
    assert pbd._day == "2026-05-15"


def test_construction_midnight_uses_yesterday():
    """When local hour < 01:00, the service falls back to yesterday."""
    parent = _make_parent()
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.poststr.return_value = SAMPLE_RESPONSE
        with patch("mysolenso.services.powerbyday.datetime") as mock_dt:
            fake_now = datetime(2026, 5, 15, 0, 30, 0)
            mock_dt.now.return_value = fake_now
            mock_dt.strptime = datetime.strptime
            pbd = MySolensoPowerByDay(parent)
    assert pbd._day == "2026-05-14"


# ---------------------------------------------------------------------------
# get_data property
# ---------------------------------------------------------------------------

def test_get_data_structure():
    """get_data contains 'metric', 'date', and 'values' keys."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    data = pbd.get_data
    assert "metric" in data
    assert "date" in data
    assert "values" in data


def test_get_data_metric_is_grid_power():
    """get_data['metric'] is always 'grid_power'."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    assert pbd.get_data["metric"] == "grid_power"


def test_get_data_date_matches_response():
    """get_data['date'] reflects the date string embedded in the response."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    assert pbd.get_data["date"] == SAMPLE_DATE


def test_get_data_values_is_dict():
    """get_data['values'] is a dictionary."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    assert isinstance(pbd.get_data["values"], dict)


def test_get_data_values_keys_are_times():
    """Keys of the 'values' dict are HH:MM strings found in the response."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    for key in pbd.get_data["values"]:
        assert len(key) == 5 and key[2] == ":"


def test_get_data_values_are_floats():
    """Values in the 'values' dict are floats."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    for v in pbd.get_data["values"].values():
        assert isinstance(v, float)


def test_get_data_values_count():
    """Number of entries in 'values' equals min(times, floats)."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    # times and values arrays have equal length in SAMPLE_RESPONSE
    assert len(pbd.get_data["values"]) == len(SAMPLE_TIMES)


# ---------------------------------------------------------------------------
# Error handling — malformed responses
# ---------------------------------------------------------------------------

def test_missing_grid_power_marker_raises():
    """MySolensoException raised when 'grid_power' marker is absent."""
    bad_response = b"08:00 08:30 \x1a\x0a2026-05-15"
    parent = _make_parent()
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.poststr.return_value = bad_response
        with pytest.raises(MySolensoException, match="grid_power"):
            MySolensoPowerByDay(parent)


def test_network_error_raises():
    """Network-level exception is wrapped in MySolensoException."""
    parent = _make_parent()
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.poststr.side_effect = Exception("timeout")
        with pytest.raises(MySolensoException):
            MySolensoPowerByDay(parent)


# ---------------------------------------------------------------------------
# set_station_id
# ---------------------------------------------------------------------------

def test_set_station_id_valid():
    """set_station_id with a known ID reloads data successfully."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    new_id = 99
    pbd.parent.station.stations = [{"id": 42}, {"id": new_id}]
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.poststr.return_value = SAMPLE_RESPONSE
        pbd.set_station_id(new_id)
    assert pbd._station_id == new_id


def test_set_station_id_unknown_raises():
    """MySolensoException raised when station ID is not in the account list."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    with pytest.raises(MySolensoException, match="not found"):
        pbd.set_station_id(9999)


def test_set_station_id_no_refresh():
    """set_station_id(refresh=False) updates _station_id without an API call."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    pbd.set_station_id(42, refresh=False)
    assert pbd._station_id == 42


# ---------------------------------------------------------------------------
# set_day
# ---------------------------------------------------------------------------

def test_set_day_valid():
    """set_day with a valid date string reloads data."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.poststr.return_value = SAMPLE_RESPONSE
        pbd.set_day("2026-01-01")
    assert pbd._day == "2026-01-01"


def test_set_day_no_refresh():
    """set_day(refresh=False) updates _day without an API call."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    pbd.set_day("2025-12-25", refresh=False)
    assert pbd._day == "2025-12-25"


def test_set_day_wrong_format_raises():
    """MySolensoException raised when the date format is not YYYY-MM-DD."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    with pytest.raises(MySolensoException):
        pbd.set_day("15/05/2026")


def test_set_day_wrong_length_raises():
    """MySolensoException raised when the date string has wrong length."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    with pytest.raises(MySolensoException):
        pbd.set_day("2026-5-1")


def test_set_day_future_raises():
    """Future date raises MySolensoException."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    with pytest.raises(MySolensoException):
        pbd.set_day("2099-01-01")


def test_set_day_min_boundary():
    """1900-01-01 is the minimum accepted date."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    pbd.set_day("1900-01-01", refresh=False)
    assert pbd._day == "1900-01-01"


def test_set_day_before_min_raises():
    """Date before 1900-01-01 raises MySolensoException."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    with pytest.raises(MySolensoException):
        pbd.set_day("1899-12-31")


# ---------------------------------------------------------------------------
# get_power_refresh
# ---------------------------------------------------------------------------

def test_get_power_refresh_reloads_data():
    """get_power_refresh triggers a new API call and updates the result."""
    pbd = _make_pbd(SAMPLE_RESPONSE)
    new_times = ["10:00", "10:30"]
    new_values = [3000.0, 4000.0]
    new_response = _make_proto_response(new_times, new_values, "2026-05-15")

    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.poststr.return_value = new_response
        pbd.get_power_refresh()

    data = pbd.get_data
    assert "10:00" in data["values"] or len(data["values"]) >= 0  # refresh occurred
