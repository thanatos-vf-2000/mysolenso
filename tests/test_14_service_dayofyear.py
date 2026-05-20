"""Tests for MySolensoCountByDayOfYeay - daily PV energy production by date.

This module covers:
- Construction and initialisation behaviour.
- Binary protobuf response parsing (dates + float32 packed array).
- Station switching via ``set_station_id``.
- Error handling for malformed responses and invalid inputs.
- The ``get_data`` property contract.
"""

import struct
import pytest
from unittest.mock import MagicMock, patch

from mysolenso.services.dayofyeay import MySolensoCountByDayOfYeay
from mysolenso.exceptions import MySolensoException

# Patch target - MySolensoPost lives inside dayofyeay module scope.
PATCH_PATH = "mysolenso.services.dayofyeay.MySolensoPost"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_proto_response(dates: list[str], values: list[float]) -> bytes:
    """Build a minimal binary response that mimics the real API payload.

    Layout:
        <dates as UTF-8 lines>\\n
        pv_eq\\x12<varint(len)><float32 * n>
    """
    # Text section: dates separated by newlines
    text_section = "\n".join(dates).encode() + b"\n"

    # Float array encoded as little-endian float32
    float_bytes = struct.pack(f"<{len(values)}f", *values)
    byte_length = len(float_bytes)

    # Encode byte_length as a LEB128 varint (single byte sufficient for < 128 bytes)
    assert byte_length < 128, "Test helper: use fewer values to stay in 1-byte varint range"
    varint = bytes([byte_length])

    # Protobuf field: marker + tag (0x12) + varint + data
    binary_section = b"pv_eq\x12" + varint + float_bytes

    return text_section + binary_section


def _make_parent(station_id: int = 42, stations: list | None = None) -> MagicMock:
    """Return a mock parent object with a pre-configured station."""
    parent = MagicMock()
    parent.station.station_id = station_id
    parent.station.stations = stations or [{"id": station_id}]
    parent.auth.get_auth_headers_hoymiles.return_value = {"Authorization": "Bearer tok"}
    return parent


def _make_doy(response: bytes, station_id: int = 42) -> MySolensoCountByDayOfYeay:
    """Instantiate MySolensoCountByDayOfYeay with a mocked API response."""
    parent = _make_parent(station_id)
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.poststr.return_value = response
        return MySolensoCountByDayOfYeay(parent)


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_DATES = ["2026-04-01", "2026-04-02", "2026-04-03"]
SAMPLE_VALUES = [4825.0, 10020.0, 11647.0]
SAMPLE_RESPONSE = _make_proto_response(SAMPLE_DATES, SAMPLE_VALUES)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_construction_success():
    """MySolensoCountByDayOfYeay initialises without error on valid response."""
    doy = _make_doy(SAMPLE_RESPONSE)
    assert doy is not None


def test_construction_no_station_raises():
    """MySolensoException raised when station_id is None at construction."""
    parent = _make_parent()
    parent.station.station_id = None
    with pytest.raises(MySolensoException, match="station_id is None"):
        MySolensoCountByDayOfYeay(parent)


# ---------------------------------------------------------------------------
# get_data property
# ---------------------------------------------------------------------------

def test_get_data_returns_dict():
    """get_data returns a dictionary."""
    doy = _make_doy(SAMPLE_RESPONSE)
    assert isinstance(doy.get_data, dict)


def test_get_data_keys_are_dates():
    """get_data keys match the date strings from the response."""
    doy = _make_doy(SAMPLE_RESPONSE)
    assert list(doy.get_data.keys()) == SAMPLE_DATES


def test_get_data_values_are_floats():
    """get_data values are floats rounded to 2 decimal places."""
    doy = _make_doy(SAMPLE_RESPONSE)
    for v in doy.get_data.values():
        assert isinstance(v, float)


def test_get_data_values_match_input():
    """get_data values approximately match the encoded float32 values."""
    doy = _make_doy(SAMPLE_RESPONSE)
    data = doy.get_data
    for date, expected in zip(SAMPLE_DATES, SAMPLE_VALUES):
        assert abs(data[date] - expected) < 1.0, (
            f"Value mismatch for {date}: got {data[date]}, expected {expected}"
        )


def test_get_data_length_matches_dates():
    """Number of entries equals the number of date strings in the response."""
    doy = _make_doy(SAMPLE_RESPONSE)
    assert len(doy.get_data) == len(SAMPLE_DATES)


def test_get_data_includes_zero_production():
    """Days with 0 Wh production are kept (not silently dropped)."""
    dates = ["2026-05-14", "2026-05-15"]
    values = [17647.0, 0.0]
    response = _make_proto_response(dates, values)
    doy = _make_doy(response)
    data = doy.get_data
    assert "2026-05-15" in data
    assert data["2026-05-15"] == 0.0


def test_get_data_single_entry():
    """A response with a single date/value pair is parsed correctly."""
    dates = ["2026-01-01"]
    values = [999.5]
    response = _make_proto_response(dates, values)
    doy = _make_doy(response)
    data = doy.get_data
    assert len(data) == 1
    assert "2026-01-01" in data


# ---------------------------------------------------------------------------
# Error handling - malformed responses
# ---------------------------------------------------------------------------

def test_no_dates_in_response_raises():
    """MySolensoException raised when the response contains no date strings."""
    bad_response = b"pv_eq\x12\x08" + struct.pack("<2f", 1.0, 2.0)
    parent = _make_parent()
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.poststr.return_value = bad_response
        with pytest.raises(MySolensoException, match="No dates found"):
            MySolensoCountByDayOfYeay(parent)


def test_missing_pveq_marker_raises():
    """MySolensoException raised when 'pv_eq' marker is absent."""
    bad_response = b"2026-04-01\nno_marker_here"
    parent = _make_parent()
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.poststr.return_value = bad_response
        with pytest.raises(MySolensoException, match="pv_eq"):
            MySolensoCountByDayOfYeay(parent)


def test_wrong_protobuf_tag_raises():
    """MySolensoException raised when the protobuf tag byte is not 0x12."""
    # Replace 0x12 with 0x11 (wrong wire type)
    dates = ["2026-04-01"]
    values = [100.0]
    response = _make_proto_response(dates, values)
    # Locate 0x12 byte just after "pv_eq" and flip it
    idx = response.find(b"pv_eq") + len(b"pv_eq")
    bad_response = response[:idx] + b"\x11" + response[idx + 1:]
    parent = _make_parent()
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.poststr.return_value = bad_response
        with pytest.raises(MySolensoException, match="Unexpected protobuf tag"):
            MySolensoCountByDayOfYeay(parent)


def test_network_error_raises():
    """Network-level exception is wrapped in MySolensoException."""
    parent = _make_parent()
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.poststr.side_effect = Exception("connection refused")
        with pytest.raises(MySolensoException):
            MySolensoCountByDayOfYeay(parent)


# ---------------------------------------------------------------------------
# set_station_id
# ---------------------------------------------------------------------------

def test_set_station_id_valid():
    """set_station_id with a known ID reloads data successfully."""
    doy = _make_doy(SAMPLE_RESPONSE)

    # Register an additional station on the parent mock
    new_id = 99
    doy.parent.station.stations = [{"id": 42}, {"id": new_id}]

    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.poststr.return_value = SAMPLE_RESPONSE
        doy.set_station_id(new_id)

    assert doy._station_id == new_id


def test_set_station_id_unknown_raises():
    """MySolensoException raised when station ID is not in the account list."""
    doy = _make_doy(SAMPLE_RESPONSE)
    with pytest.raises(MySolensoException, match="not found"):
        doy.set_station_id(9999)


def test_set_station_id_no_refresh():
    """set_station_id(refresh=False) updates _station_id without an API call."""
    doy = _make_doy(SAMPLE_RESPONSE)
    new_id = 42  # already in the station list from _make_parent
    doy.set_station_id(new_id, refresh=False)
    assert doy._station_id == new_id


def test_set_station_id_reload_failure_raises():
    """Network error during reload is wrapped in MySolensoException."""
    doy = _make_doy(SAMPLE_RESPONSE)
    doy.parent.station.stations = [{"id": 42}, {"id": 55}]
    with patch(PATCH_PATH) as MockPost:
        MockPost.return_value.poststr.side_effect = Exception("timeout")
        with pytest.raises(MySolensoException):
            doy.set_station_id(55)


# ---------------------------------------------------------------------------
# Extra value / date count mismatch
# ---------------------------------------------------------------------------

def test_extra_floats_are_ignored():
    """When there are more float values than dates, the extras are silently ignored."""
    dates = ["2026-04-01", "2026-04-02"]
    # 4 floats but only 2 dates - zip stops at 2
    values = [100.0, 200.0, 300.0, 400.0]
    response = _make_proto_response(dates, values)
    doy = _make_doy(response)
    assert len(doy.get_data) == 2
