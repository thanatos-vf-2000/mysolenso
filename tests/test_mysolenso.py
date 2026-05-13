import pytest
from unittest.mock import patch

from mysolenso import MySolenso


def test_mysolenso_init_with_token():

    client = MySolenso(
        username="admin",
        token="abc123"
    )

    assert client.username == "admin"

    # Vérifie le sous-module auth
    assert client.auth is not None
    assert client.auth.isConnect() is True
    assert client.auth.token == "abc123"


@patch("mysolenso.auth.MySolensoAuth._authenticate")
def test_mysolenso_init_with_password(mock_auth):

    client = MySolenso(
        username="admin",
        password="encrypted-password"
    )

    assert client.username == "admin"
    assert client.password == "encrypted-password"

    # Vérifie que l'authentification est appelée
    mock_auth.assert_called_once_with("encrypted-password")


def test_mysolenso_auth_headers():

    client = MySolenso(
        username="admin",
        token="mytoken"
    )

    headers = client.auth.get_auth_headers_hoymiles()

    assert headers == {
        "Authorization": "Bearer mytoken"
    }


def test_mysolenso_disconnect():

    client = MySolenso(
        username="admin",
        token="mytoken"
    )

    assert client.auth.isConnect() is True

    client.auth.disconnect()

    assert client.auth.isConnect() is False
    assert client.auth.token == ""


def test_mysolenso_auth_property_exists():

    client = MySolenso(
        username="admin",
        token="abc123"
    )

    assert hasattr(client, "auth")