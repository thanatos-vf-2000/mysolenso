"""MySolenso Auth library for Python.

Source: https://github.com/thanatos-vf-2000/mysolenso

Init MySolenso connection.

    Args:
        username (str): Username
        password Optional(str): Password (Crypt)
        token Optional(str): Token

    Raises:
        KeyError: 
        
"""
from __future__ import annotations
import logging


import threading
from typing import Optional

import requests
from requests import Response
from requests.exceptions import RequestException, Timeout

from .exceptions import (
    MySolensoException,
    MySolensoConnectionException,
    MySolensoAuthenticationException,
)
from .const import (
    DEFAULT_TIMEOUT,
    API_AUTH_LOGIN,
)

_LOG = logging.getLogger(__name__)

class MySolensoAuth:
    """
    Client sécurisé et robuste pour l'API Solenso.
    """
    
    def __init__(
        self,
        username: str,
        password: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:

        if not username or not username.strip():
            raise MySolensoConnectionException("The ‘username’ field is required.")

        if password is None and token is None:
            raise MySolensoConnectionException(
                "You must provide either an encrypted password or a token."
            )

        self.username = username.strip()
        self._token = token.strip() if token else ""
        
        self._token_language = "fr_fr"

        self._lock = threading.Lock()

        self._session = requests.Session()

        self._session.headers.update({
            "User-Agent": "MySolenso/1.0",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
        })

        # Auth automatique si password fourni
        if password:
            self._authenticate(password)

    @property
    def token(self) -> str:
        """
        Retourne le token courant.
        """
        return self._token
    
    @property
    def token_language(self) -> str:
        """
        Retourne le _token_language courant.
        """
        return self._token_language
    

    def isConnect(self) -> bool:
        """
        Vérifie si un token valide est présent.
        """
        return bool(self._token and self._token.strip())
    
    def _authenticate(self, password: str) -> None:
        """
        Authentification API avec format RAW spécifique.
        """

        raw_payload = {
            "ERROR_BACK": True,
            "LOAD": {
                "loading": True
            },
            "body": {
                "user_name": self.username,
                "password": password
            },
            "WAITING_PROMISE": True
        }

        try:
            response = self._post(
                API_AUTH_LOGIN,
                json=raw_payload,
            )

            data = self._safe_json(response)

            # Vérification stricte du retour API
            status = str(data.get("status", "")).strip()
            message = str(data.get("message", "")).strip().lower()

            if status != "0":
                raise MySolensoAuthenticationException(
                    f"API error - status={status}, message={data.get('message')}"
                )

            if message != "success":
                raise MySolensoAuthenticationException(
                    f"Authentication failed - message={data.get('message')}"
                )

            token = (
                data.get("data", {})
                .get("token", "")
                .strip()
            )

            if not token:
                raise MySolensoAuthenticationException(
                    "Token missing from the API response."
                )

            with self._lock:
                self._token = token

        except Timeout as exc:
            raise MySolensoException(
                "Timeout during authentication."
            ) from exc

        except RequestException as exc:
            raise MySolensoException(
                f"Network/API error: {exc}"
            ) from exc
            
    def _post(self, url: str, **kwargs) -> Response:
        """
        POST robuste avec timeout forcé.
        """

        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)

        response = self._session.post(url, **kwargs)

        # Vérifie les erreurs HTTP
        response.raise_for_status()

        return response

    @staticmethod
    def _safe_json(response: Response) -> dict:
        """
        Parse JSON sécurisé.
        """

        try:
            data = response.json()

            if not isinstance(data, dict):
                raise ValueError("Invalid JSON response.")

            return data

        except ValueError as exc:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from exc

    def get_auth_headers_solenso(self) -> dict:
        """
        Retourne les headers Authorization.
        """

        if not self.isConnect():
            raise MySolensoAuthenticationException(
                "No tokens available."
            )

        return {
            "Cookie": f"solenso_token_language={self._token_language}; solenso_token={self._token}"
        }
        
    def get_auth_headers_hoymiles(self) -> dict:
        """
        Retourne les headers Authorization.
        """

        if not self.isConnect():
            raise MySolensoAuthenticationException(
                "No tokens available."
            )

        return {
            "Authorization": f"{self._token}"
        }

    def disconnect(self) -> None:
        """
        Supprime le token mémoire.
        """

        with self._lock:
            self._token = ""

    def __repr__(self) -> str:
        """
        Évite d'exposer les secrets dans les logs.
        """

        return (
            f"{self.__class__.__name__}("
            f"utilisateur='{self.utilisateur}', "
            f"isConnected={self.isConnect()})"
        )
    