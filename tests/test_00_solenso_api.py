"""Tests for MySolensoAuth - authentication, headers, and session lifecycle."""

import pytest
from unittest.mock import Mock, patch

from mysolenso.auth import MySolensoAuth
from mysolenso.exceptions import (
    MySolensoException,
    MySolensoConnectionException,
    MySolensoAuthenticationException,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_response(status="0", message="success", data=None, raise_status=None):
    """Build a mock requests.Response for the auth endpoint."""
    resp = Mock()
    resp.json.return_value = {
        "status":        status,
        "message":       message,
        "data":          data or {},
        "systemNotice":  None,
    }
    if raise_status:
        resp.raise_for_status.side_effect = raise_status
    else:
        resp.raise_for_status.return_value = None
    return resp


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_init_with_token():
    """Token is stored and session is connected."""
    client = MySolensoAuth(username="admin", token="abc123")

    assert client.isConnect() is True
    assert client.token == "abc123"
    assert client.username == "admin"


def test_init_strips_whitespace():
    """Username and token are stripped of leading/trailing spaces."""
    client = MySolensoAuth(username="  admin  ", token="  tok  ")

    assert client.username == "admin"
    assert client.token == "tok"


def test_init_without_username():
    """Empty username raises MySolensoConnectionException."""
    with pytest.raises(MySolensoConnectionException):
        MySolensoAuth(username="", token="abc123")


def test_init_blank_username():
    """Whitespace-only username raises MySolensoConnectionException."""
    with pytest.raises(MySolensoConnectionException):
        MySolensoAuth(username="   ", token="abc123")


def test_init_without_password_or_token():
    """Missing both password and token raises MySolensoConnectionException."""
    with pytest.raises(MySolensoConnectionException):
        MySolensoAuth(username="admin")


# ---------------------------------------------------------------------------
# Password-based authentication
# ---------------------------------------------------------------------------

@patch("requests.Session.post")
def test_auth_success(mock_post):
    """Successful auth stores the returned token."""
    mock_post.return_value = _fake_response(data={"token": "mytoken123"})

    client = MySolensoAuth(username="admin", password="encrypted-password")

    assert client.isConnect() is True
    assert client.token == "mytoken123"


@patch("requests.Session.post")
def test_auth_invalid_status(mock_post):
    """Non-zero API status raises MySolensoAuthenticationException."""
    mock_post.return_value = _fake_response(status="401", message="bad credentials")

    with pytest.raises(MySolensoAuthenticationException) as exc:
        MySolensoAuth(username="admin", password="bad-password")

    assert "401" in str(exc.value)
    assert "bad credentials" in str(exc.value)


@patch("requests.Session.post")
def test_auth_invalid_message(mock_post):
    """status=0 but message != 'success' raises MySolensoAuthenticationException."""
    mock_post.return_value = _fake_response(status="0", message="failed")

    with pytest.raises(MySolensoAuthenticationException):
        MySolensoAuth(username="admin", password="bad-password")


@patch("requests.Session.post")
def test_auth_missing_token(mock_post):
    """Success response with empty token raises MySolensoAuthenticationException."""
    mock_post.return_value = _fake_response(data={})

    with pytest.raises(MySolensoAuthenticationException):
        MySolensoAuth(username="admin", password="encrypted-password")


@patch("requests.Session.post")
def test_auth_invalid_json(mock_post):
    """Non-JSON response raises MySolensoException."""
    resp = Mock()
    resp.json.side_effect = ValueError("invalid json")
    resp.raise_for_status.return_value = None
    mock_post.return_value = resp

    with pytest.raises(MySolensoException):
        MySolensoAuth(username="admin", password="encrypted-password")


@patch("requests.Session.post")
def test_auth_non_dict_json(mock_post):
    """List JSON response (not a dict) raises MySolensoException."""
    resp = Mock()
    resp.json.return_value = ["unexpected", "list"]
    resp.raise_for_status.return_value = None
    mock_post.return_value = resp

    with pytest.raises(MySolensoException):
        MySolensoAuth(username="admin", password="encrypted-password")


@patch("requests.Session.post")
def test_auth_network_timeout(mock_post):
    """Timeout during authentication raises MySolensoException."""
    from requests.exceptions import Timeout
    mock_post.side_effect = Timeout()

    with pytest.raises(MySolensoException):
        MySolensoAuth(username="admin", password="encrypted-password")


@patch("requests.Session.post")
def test_auth_http_error(mock_post):
    """HTTP 500 during authentication raises MySolensoException."""
    from requests.exceptions import RequestException
    mock_post.side_effect = RequestException("server error")

    with pytest.raises(MySolensoException):
        MySolensoAuth(username="admin", password="encrypted-password")


# ---------------------------------------------------------------------------
# Session lifecycle
# ---------------------------------------------------------------------------

def test_disconnect_clears_token():
    """disconnect() sets token to empty and isConnect() returns False."""
    client = MySolensoAuth(username="admin", token="abc123")

    assert client.isConnect() is True
    client.disconnect()

    assert client.isConnect() is False
    assert client.token == ""


def test_is_connect_false_when_token_empty():
    """isConnect() returns False when token is an empty string."""
    client = MySolensoAuth(username="admin", token="x")
    client._token = ""

    assert client.isConnect() is False


def test_is_connect_false_when_token_blank():
    """isConnect() returns False when token is only whitespace."""
    client = MySolensoAuth(username="admin", token="x")
    client._token = "   "

    assert client.isConnect() is False


# ---------------------------------------------------------------------------
# Authorisation headers
# ---------------------------------------------------------------------------

def test_get_auth_headers_hoymiles():
    """get_auth_headers_hoymiles returns a correct Bearer header."""
    client = MySolensoAuth(username="admin", token="abc123")

    assert client.get_auth_headers_hoymiles() == {"Authorization": "abc123"}


def test_get_auth_headers_solenso():
    """get_auth_headers_solenso returns the correct Cookie header."""
    client = MySolensoAuth(username="admin", token="abc123")
    headers = client.get_auth_headers_solenso()

    assert "Cookie" in headers
    assert "solenso_token=abc123" in headers["Cookie"]
    assert "solenso_token_language=" in headers["Cookie"]


def test_get_auth_headers_hoymiles_without_token():
    """get_auth_headers_hoymiles raises when disconnected."""
    client = MySolensoAuth(username="admin", token="abc123")
    client.disconnect()

    with pytest.raises(MySolensoAuthenticationException):
        client.get_auth_headers_hoymiles()


def test_get_auth_headers_solenso_without_token():
    """get_auth_headers_solenso raises when disconnected."""
    client = MySolensoAuth(username="admin", token="abc123")
    client.disconnect()

    with pytest.raises(MySolensoAuthenticationException):
        client.get_auth_headers_solenso()


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------

def test_repr_connected():
    """repr shows username and connected=True."""
    client = MySolensoAuth(username="admin", token="tok")
    r = repr(client)

    assert "admin" in r
    assert "True" in r


def test_repr_disconnected():
    """repr shows connected=False after disconnect."""
    client = MySolensoAuth(username="admin", token="tok")
    client.disconnect()

    assert "False" in repr(client)
