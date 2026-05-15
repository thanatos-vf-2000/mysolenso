"""Tests for MySolensoMe — user profile service."""

import pytest
from unittest.mock import MagicMock, patch

from mysolenso.services.me import MySolensoMe
from mysolenso.exceptions import MySolensoException


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_parent(api_data: dict):
    """Return a mock parent whose MySolensoPost will return api_data."""
    parent = MagicMock()
    parent.auth.get_auth_headers_solenso.return_value = {
        "Cookie": "solenso_token=tok"
    }
    with patch("mysolenso.services.me.MySolensoPost") as MockPost:
        instance = MockPost.return_value
        instance.post.return_value = api_data
        yield parent, MockPost


@pytest.fixture
def full_response():
    return {
        "user_name":  "JDOE",
        "name":       "John Doe",
        "phone":      "+33600000000",
        "email":      "jdoe@jdoe.com",
        "role_ids":   "1",
        "roles":      [{"name": "Administrator"}],
        "group":      {"name": "My Group"},
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_me(api_data: dict) -> MySolensoMe:
    parent = MagicMock()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "tok"}
    with patch("mysolenso.services.me.MySolensoPost") as MockPost:
        MockPost.return_value.post.return_value = api_data
        return MySolensoMe(parent)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

def test_me_username(full_response):
    me = _make_me(full_response)
    assert me.username == "JDOE"


def test_me_name(full_response):
    me = _make_me(full_response)
    assert me.name == "John Doe"


def test_me_phone(full_response):
    me = _make_me(full_response)
    assert me.phone == "+33600000000"


def test_me_email(full_response):
    me = _make_me(full_response)
    assert me.email == "jdoe@jdoe.com"


def test_me_role_ids(full_response):
    me = _make_me(full_response)
    assert me.role_ids == "1"


def test_me_roles_name(full_response):
    me = _make_me(full_response)
    assert me.roles_name == "Administrator"


def test_me_group_name(full_response):
    me = _make_me(full_response)
    assert me.group_name == "My Group"


def test_me_all_data(full_response):
    me = _make_me(full_response)
    assert me.all_data == full_response


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_me_empty_roles():
    """Empty roles list → roles_name is empty string."""
    me = _make_me({
        "user_name": "u", "name": "n", "phone": "", "email": "e",
        "role_ids": "1", "roles": [], "group": {"name": "G"},
    })
    assert me.roles_name == None


def test_me_missing_group():
    """Missing group key → group_name is empty string."""
    me = _make_me({
        "user_name": "u", "name": "n", "phone": "", "email": "e",
        "role_ids": "1", "roles": [{"name": "Admin"}],
    })
    assert me.group_name == None


def test_me_strips_whitespace():
    """String fields are stripped of whitespace."""
    me = _make_me({
        "user_name": "  admin  ", "name": "  Franck  ", "phone": "",
        "email": "  e@e.com  ", "role_ids": " 1 ",
        "roles": [{"name": "  Admin  "}], "group": {"name": "  G  "},
    })
    assert me.username == "admin"
    assert me.name == "Franck"
    assert me.email == "e@e.com"
    assert me.roles_name == "Admin"
    assert me.group_name == "G"


def test_me_api_error_raises():
    """API exception is wrapped in MySolensoException."""
    parent = MagicMock()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "tok"}
    with patch("mysolenso.services.me.MySolensoPost") as MockPost:
        MockPost.return_value.post.side_effect = Exception("network error")
        with pytest.raises(MySolensoException):
            MySolensoMe(parent)


def test_me_headers_injected(full_response):
    """Session headers from auth are passed to MySolensoPost."""
    parent = MagicMock()
    parent.auth.get_auth_headers_solenso.return_value = {"Cookie": "solenso_token=xyz"}
    with patch("mysolenso.services.me.MySolensoPost") as MockPost:
        instance = MockPost.return_value
        instance.post.return_value = full_response
        MySolensoMe(parent)
        instance.set_headers.assert_called_once_with({"Cookie": "solenso_token=xyz"})
