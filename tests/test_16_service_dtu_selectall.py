"""Tests for MySolensoDTUSelectAll — DTU and microinverter list service."""
 
import pytest
from unittest.mock import MagicMock, patch
 
from mysolenso.services.dtu.selectall import MySolensoDTUSelectAll
from mysolenso.exceptions import MySolensoException
 
 
# ---------------------------------------------------------------------------
# Fixtures / sample data
# ---------------------------------------------------------------------------
 
MICROS = [
    {"sn": "A110016B1", "id": 6654220, "vc": "2BD", "dev_type": 3, "port_array": [1, 2]},
    {"sn": "A110016GV", "id": 6654230, "vc": "23D", "dev_type": 3, "port_array": [1, 2]},
]
 
FULL_RESPONSE = [
    {
        "dtu": {
            "id": 1456060,
            "sn": "D0100289H",
            "dev_type": 1,
            "vc": "289",
        },
        "repeater_list": [
            {
                "id": 0,
                "sn": "",
                "dev_type": 2,
                "micros": MICROS,
            }
        ],
    }
]
 
 
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def _make_parent(station_id=42, stations=None, api_response=None):
    """Build a mock parent that satisfies MySolensoDTUSelectAll.__init__."""
    parent = MagicMock()
    parent.station.station_id = station_id
    parent.station.stations = stations or [{"id": station_id}]
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "solenso_token=tok"}
    return parent
 
 
def _make_dtu_selectall(api_response=None) -> MySolensoDTUSelectAll:
    """Build a MySolensoDTUSelectAll with a mocked POST response."""
    parent = _make_parent()
    response = api_response if api_response is not None else FULL_RESPONSE
    with patch("mysolenso.services.dtu.selectall.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = response
        obj = MySolensoDTUSelectAll(parent)
        obj._get_dtu_select_all()
        return obj
 
 
# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------
 
def test_init_raises_when_no_station():
    """MySolensoDTUSelectAll raises if no active station is set."""
    parent = _make_parent(station_id=None)
    with pytest.raises(MySolensoException):
        MySolensoDTUSelectAll(parent)
 
 
def test_init_stores_station_id():
    """station_id is inherited from the parent on construction."""
    parent = _make_parent(station_id=99)
    with patch("mysolenso.services.dtu.selectall.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoDTUSelectAll(parent)
        obj._get_dtu_select_all()
        assert obj._station_id == 99
 
 
# ---------------------------------------------------------------------------
# Properties — DTU
# ---------------------------------------------------------------------------
 
def test_dtu_id():
    obj = _make_dtu_selectall()
    assert obj.dtu_id == 1456060
 
 
def test_dtu_sn():
    obj = _make_dtu_selectall()
    assert obj.dtu_sn == "D0100289H"
 
 
def test_dtu_dev_type():
    obj = _make_dtu_selectall()
    assert obj.dtu_dev_type == 1
 
 
def test_dtu_vc():
    obj = _make_dtu_selectall()
    assert obj.dtu_vc == "289"
 
 
def test_all_data():
    obj = _make_dtu_selectall()
    assert obj.all_data == FULL_RESPONSE[0]
 
 
# ---------------------------------------------------------------------------
# Properties — microinverters
# ---------------------------------------------------------------------------
 
def test_list_micros_info_length():
    obj = _make_dtu_selectall()
    assert len(obj.list_micros_info) == 2
 
 
def test_list_micros_info_content():
    obj = _make_dtu_selectall()
    assert obj.list_micros_info[0]["sn"] == "A110016B1"
    assert obj.list_micros_info[1]["id"] == 6654230
 
 
def test_list_micros_projection():
    """list_micros returns only sn and id."""
    obj = _make_dtu_selectall()
    micros = obj.list_micros
    assert micros == [
        {"sn": "A110016B1", "id": 6654220},
        {"sn": "A110016GV", "id": 6654230},
    ]
 
 
def test_list_micros_raises_when_empty():
    """list_micros raises ValueError when microinverter list is empty."""
    obj = _make_dtu_selectall(api_response=[{
        "dtu": {"id": 1, "sn": "X", "dev_type": 1, "vc": "1"},
        "repeater_list": [{"id": 0, "sn": "", "dev_type": 2, "micros": []}],
    }])
    with pytest.raises(ValueError):
        _ = obj.list_micros
 
 
# ---------------------------------------------------------------------------
# set_station
# ---------------------------------------------------------------------------
 
def test_set_station_invalid_raises():
    """set_station raises when the requested station ID is not in the list."""
    parent = _make_parent(station_id=42, stations=[{"id": 42}])
    with patch("mysolenso.services.dtu.selectall.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoDTUSelectAll(parent)
        obj._get_dtu_select_all()
        with pytest.raises(MySolensoException):
            obj.set_station(999, refresh=False)
 
 
def test_set_station_updates_id():
    """set_station stores the new station ID without refreshing."""
    parent = _make_parent(station_id=42, stations=[{"id": 42}, {"id": 43}])
    with patch("mysolenso.services.dtu.selectall.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoDTUSelectAll(parent)
        obj._get_dtu_select_all()
        obj.set_station(43, refresh=False)
        assert obj._station_id == 43
 
 
def test_set_station_with_refresh_calls_api():
    """set_station with refresh=True triggers a new API call."""
    parent = _make_parent(station_id=42, stations=[{"id": 42}, {"id": 43}])
    with patch("mysolenso.services.dtu.selectall.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoDTUSelectAll(parent)
        obj._get_dtu_select_all()
        initial_call_count = MockPost.return_value.post.call_count
        obj.set_station(43, refresh=True)
        assert MockPost.return_value.post.call_count > initial_call_count
 
 
# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------
 
def test_dtu_select_all_refresh_updates_data():
    """dtu_select_all_refresh fetches fresh data from the API."""
    parent = _make_parent()
    with patch("mysolenso.services.dtu.selectall.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoDTUSelectAll(parent)
        obj._get_dtu_select_all()
        obj.dtu_select_all_refresh()
        assert MockPost.return_value.post.call_count >= 2
 
 
# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------
 
def test_empty_response_raises():
    """Empty API response raises MySolensoException."""
    parent = _make_parent()
    with patch("mysolenso.services.dtu.selectall.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = []
        obj = MySolensoDTUSelectAll(parent)
        with pytest.raises(MySolensoException):
            obj._get_dtu_select_all()
 
 
def test_network_error_raises():
    """Network error during API call raises MySolensoException."""
    parent = _make_parent()
    with patch("mysolenso.services.dtu.selectall.MySolensoPost") as MockPost:
        MockPost.return_value.post.side_effect = Exception("connection refused")
        obj = MySolensoDTUSelectAll(parent)
        with pytest.raises(MySolensoException):
            obj._get_dtu_select_all()
 
 
def test_headers_injected():
    """Auth headers from the parent are forwarded to MySolensoPost."""
    parent = _make_parent()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "solenso_token=xyz"}
    with patch("mysolenso.services.dtu.selectall.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoDTUSelectAll(parent)
        obj._get_dtu_select_all()
        MockPost.return_value.set_headers.assert_called_with({"Cookie": "solenso_token=xyz"})
 
 
def test_whitespace_stripped_from_sn():
    """String fields are stripped of leading/trailing whitespace."""
    response = [{
        "dtu": {"id": 1, "sn": "  D0100289H  ", "dev_type": 1, "vc": "  289  "},
        "repeater_list": [{"id": 0, "sn": "", "dev_type": 2, "micros": MICROS}],
    }]
    obj = _make_dtu_selectall(api_response=response)
    assert obj.dtu_sn == "D0100289H"
    assert obj.dtu_vc == "289"