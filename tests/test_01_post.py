"""Tests for MySolensoPost - low-level POST helper."""

import pytest
from unittest.mock import Mock, patch
from requests.exceptions import Timeout

from mysolenso.post import MySolensoPost
from mysolenso.exceptions import (
    MySolensoException,
    MySolensoAuthenticationException,
)


def _response(payload):
    resp = Mock()
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


def test_default_headers_exist():
    client = MySolensoPost()

    assert "User-Agent" in client.headers
    assert "Content-Type" in client.headers


def test_set_header_updates_value():
    client = MySolensoPost()

    client.set_header("Authorization", "Bearer token")

    assert client.headers["Authorization"] == "Bearer token"


@patch("mysolenso.post.requests.Session.post")
def test_post_returns_data(mock_post):
    mock_post.return_value = _response({
        "status": "0",
        "message": "success",
        "data": {"ok": True},
    })

    client = MySolensoPost()

    result = client.post("https://example.com")

    assert result == {"ok": True}


@patch("mysolenso.post.requests.Session.post")
def test_post_raises_authentication_error(mock_post):
    mock_post.return_value = _response({
        "status": "1",
        "message": "unauthorized",
    })

    client = MySolensoPost()

    with pytest.raises(MySolensoAuthenticationException):
        client.post("https://example.com")


@patch("mysolenso.post.requests.Session.post")
def test_post_raises_timeout(mock_post):
    mock_post.side_effect = Timeout()

    client = MySolensoPost()

    with pytest.raises(MySolensoException):
        client.post("https://example.com")
