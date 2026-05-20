"""Tests for MySolensoDTUFind - single DTU detail service."""
 
import pytest
from unittest.mock import MagicMock, patch
 
from mysolenso.services.dtu.find import MySolensoDTUFind
from mysolenso.exceptions import MySolensoException
 
 
# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------
 
DTU_ID = 1456060
 
FULL_RESPONSE = {
    "id": DTU_ID,
    "sid": 1553580,
    "station_name": "DOE JOHN",
    "sn": "D0100289H",
    "dev_type": 1,
    "tz_name": "UTC+01",
    "vc": "289",
    "init_soft_ver": "V00.00.06",
    "init_hard_ver": "H12.02.02",
    "mi_num": 5,
    "rule": {"module_no": "HD-Insight"},
}
 
 
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def _make_parent(station_id=42, dtu_id=DTU_ID):
    """Return a mock parent with a station and a dtuselectall stub."""
    parent = MagicMock()
    parent.station.station_id = station_id
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "solenso_token=tok"}
    parent.dtuselectall.dtu_id = dtu_id
    return parent
 
 
def _make_dtu_find(dtu_id=DTU_ID, api_response=None) -> MySolensoDTUFind:
    """Build a MySolensoDTUFind with set_dtu already called."""
    parent = _make_parent(dtu_id=dtu_id)
    response = api_response if api_response is not None else FULL_RESPONSE
    with patch("mysolenso.services.dtu.find.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = response
        obj = MySolensoDTUFind(parent)
        obj.set_dtu(dtu_id, refresh=True)
        return obj
 
 
# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------
 
def test_init_raises_when_no_station():
    """MySolensoDTUFind raises if no active station is set on the parent."""
    parent = _make_parent(station_id=None)
    with pytest.raises(MySolensoException):
        MySolensoDTUFind(parent)
 
 
def test_init_stores_station_id():
    """station_id is read from the parent at construction."""
    parent = _make_parent(station_id=55)
    obj = MySolensoDTUFind(parent)
    assert obj._station_id == 55
 
 
def test_init_dtu_id_is_none():
    """_dtu_id is None until set_dtu is called."""
    parent = _make_parent()
    obj = MySolensoDTUFind(parent)
    assert obj._dtu_id is None
 
 
# ---------------------------------------------------------------------------
# set_dtu
# ---------------------------------------------------------------------------
 
def test_set_dtu_valid():
    """set_dtu stores the DTU ID when it matches dtuselectall.dtu_id."""
    parent = _make_parent(dtu_id=DTU_ID)
    with patch("mysolenso.services.dtu.find.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoDTUFind(parent)
        obj.set_dtu(DTU_ID, refresh=True)
        assert obj._dtu_id == DTU_ID
 
 
def test_set_dtu_invalid_raises():
    """set_dtu raises MySolensoException when the DTU ID doesn't match."""
    parent = _make_parent(dtu_id=DTU_ID)
    obj = MySolensoDTUFind(parent)
    with pytest.raises(MySolensoException):
        obj.set_dtu(9999999, refresh=False)
 
 
def test_set_dtu_no_refresh_skips_api():
    """set_dtu with refresh=False does not call the API."""
    parent = _make_parent(dtu_id=DTU_ID)
    with patch("mysolenso.services.dtu.find.MySolensoPost") as MockPost:
        obj = MySolensoDTUFind(parent)
        obj.set_dtu(DTU_ID, refresh=False)
        MockPost.return_value.post.assert_not_called()
 
 
def test_set_dtu_with_refresh_calls_api():
    """set_dtu with refresh=True triggers an API call."""
    parent = _make_parent(dtu_id=DTU_ID)
    with patch("mysolenso.services.dtu.find.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoDTUFind(parent)
        obj.set_dtu(DTU_ID, refresh=True)
        MockPost.return_value.post.assert_called_once()
 
 
# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------
 
def test_all_data():
    obj = _make_dtu_find()
    assert obj.all_data == FULL_RESPONSE
 
 
def test_all_data_station_name():
    obj = _make_dtu_find()
    assert obj.all_data["station_name"] == "DOE JOHN"
 
 
def test_all_data_sn():
    obj = _make_dtu_find()
    assert obj.all_data["sn"] == "D0100289H"
 
 
def test_all_data_mi_num():
    obj = _make_dtu_find()
    assert obj.all_data["mi_num"] == 5
 
 
# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------
 
def test_get_dtu_find_raises_when_dtu_id_none():
    """_get_dtu_find raises MySolensoException if _dtu_id is None."""
    parent = _make_parent()
    obj = MySolensoDTUFind(parent)
    # _dtu_id is None by default - calling the private method directly
    with pytest.raises(MySolensoException):
        obj._get_dtu_find()
 
 
def test_empty_response_raises():
    """Empty API response raises MySolensoException."""
    parent = _make_parent(dtu_id=DTU_ID)
    with patch("mysolenso.services.dtu.find.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = {}
        obj = MySolensoDTUFind(parent)
        obj._dtu_id = DTU_ID
        with pytest.raises(MySolensoException):
            obj._get_dtu_find()
 
 
def test_network_error_raises():
    """Network error during API call raises MySolensoException."""
    parent = _make_parent(dtu_id=DTU_ID)
    with patch("mysolenso.services.dtu.find.MySolensoPost") as MockPost:
        MockPost.return_value.post.side_effect = Exception("timeout")
        obj = MySolensoDTUFind(parent)
        obj._dtu_id = DTU_ID
        with pytest.raises(MySolensoException):
            obj._get_dtu_find()
 
 
def test_headers_injected():
    """Auth headers from the parent are forwarded to MySolensoPost."""
    parent = _make_parent(dtu_id=DTU_ID)
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "solenso_token=xyz"}
    with patch("mysolenso.services.dtu.find.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = FULL_RESPONSE
        obj = MySolensoDTUFind(parent)
        obj.set_dtu(DTU_ID, refresh=True)
        MockPost.return_value.set_headers.assert_called_with({"Cookie": "solenso_token=xyz"})