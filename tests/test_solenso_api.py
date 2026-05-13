import pytest
from unittest.mock import Mock, patch

from mysolenso.auth import MySolensoAuth

from mysolenso.exceptions import (
    MySolensoException,
    MySolensoConnectionException,
    MySolensoAuthenticationException,
)


def test_init_with_token():
    client = MySolensoAuth(
        username="admin",
        token="abc123"
    )

    assert client.isConnect() is True
    assert client.token == "abc123"


def test_init_without_username():
    with pytest.raises(MySolensoConnectionException):
        MySolensoAuth(
            username="",
            token="abc123"
        )


def test_init_without_password_or_token():
    with pytest.raises(MySolensoConnectionException):
        MySolensoAuth(
            username="admin"
        )


@patch("requests.Session.post")
def test_auth_success(mock_post):
    fake_response = Mock()

    fake_response.json.return_value = {
        "status": "0",
        "message": "success",
        "data": {
            "token": "mytoken123"
        },
        "systemNotice": None
    }

    fake_response.raise_for_status.return_value = None

    mock_post.return_value = fake_response

    client = MySolensoAuth(
        username="admin",
        password="encrypted-password"
    )

    assert client.isConnect() is True
    assert client.token == "mytoken123"


@patch("requests.Session.post")
def test_auth_invalid_status(mock_post):
    fake_response = Mock()

    fake_response.json.return_value = {
        "status": "401",
        "message": "bad credentials",
        "data": {},
        "systemNotice": None
    }

    fake_response.raise_for_status.return_value = None

    mock_post.return_value = fake_response

    with pytest.raises(MySolensoAuthenticationException) as exc:
        MySolensoAuth(
            username="admin",
            password="bad-password"
        )

    assert "401" in str(exc.value)
    assert "bad credentials" in str(exc.value)


@patch("requests.Session.post")
def test_auth_invalid_message(mock_post):
    fake_response = Mock()

    fake_response.json.return_value = {
        "status": "0",
        "message": "failed",
        "data": {},
        "systemNotice": None
    }

    fake_response.raise_for_status.return_value = None

    mock_post.return_value = fake_response

    with pytest.raises(MySolensoAuthenticationException):
        MySolensoAuth(
            username="admin",
            password="bad-password"
        )


@patch("requests.Session.post")
def test_auth_missing_token(mock_post):
    fake_response = Mock()

    fake_response.json.return_value = {
        "status": "0",
        "message": "success",
        "data": {},
        "systemNotice": None
    }

    fake_response.raise_for_status.return_value = None

    mock_post.return_value = fake_response

    with pytest.raises(MySolensoAuthenticationException):
        MySolensoAuth(
            username="admin",
            password="encrypted-password"
        )


@patch("requests.Session.post")
def test_invalid_json_response(mock_post):
    fake_response = Mock()

    fake_response.json.side_effect = ValueError("invalid json")

    fake_response.raise_for_status.return_value = None

    mock_post.return_value = fake_response

    with pytest.raises(MySolensoException):
        MySolensoAuth(
            username="admin",
            password="encrypted-password"
        )


def test_disconnect():
    client = MySolensoAuth(
        username="admin",
        token="abc123"
    )

    assert client.isConnect() is True

    client.disconnect()

    assert client.isConnect() is False
    assert client.token == ""


def test_get_auth_headers_hoymiles():
    client = MySolensoAuth(
        username="admin",
        token="abc123"
    )

    headers = client.get_auth_headers_hoymiles()

    assert headers == {
        "Authorization": "Bearer abc123"
    }


def test_get_auth_headers_hoymiles_without_token():
    client = MySolensoAuth(
        username="admin",
        token="abc123"
    )

    client.disconnect()

    with pytest.raises(MySolensoAuthenticationException):
        client.get_auth_headers_hoymiles()