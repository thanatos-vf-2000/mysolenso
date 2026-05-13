from __future__ import annotations
import logging

from typing import Optional, Dict, Any

import requests
from requests import Response
from requests.exceptions import RequestException, Timeout

from .exceptions import (
    MySolensoException,
    MySolensoConnectionException,
    MySolensoAuthenticationException,
)

from .const import DEFAULT_TIMEOUT

_LOG = logging.getLogger(__name__)

class MySolensoPost:
    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.timeout = timeout
        
        self._headers: Dict[str, str] = {
            "User-Agent": "MySolenso/1.0",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
        }
        
        self._raw_payload: Dict[str, Any] = {}

        self._session = requests.Session()
        
    @property
    def headers(self) -> Dict[str, str]:
        """
        Retourne les headers courants.
        """
        return self._headers

    @property
    def raw_payload(self) -> Dict[str, Any]:
        """
        Retourne le payload JSON courant.
        """
        return self._raw_payload

    def set_header(
        self,
        key: str,
        value: str,
    ) -> None:
        """
        Ajoute ou modifie un header.
        """

        self._headers[key] = value

    def remove_header(
        self,
        key: str,
    ) -> None:
        """
        Supprime un header.
        """

        if key in self._headers:
            del self._headers[key]

    def set_headers(
        self,
        headers: Dict[str, str],
    ) -> None:
        """
        Fusionne plusieurs headers.
        """

        self._headers.update(headers)

    def set_raw_payload(
        self,
        payload: Dict[str, Any],
    ) -> None:
        """
        Définit le payload JSON RAW.
        """

        if not isinstance(payload, dict):
            raise MySolensoException(
                "Payload must be a dictionary."
            )

        self._raw_payload = payload

    def post(
        self,
        url: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """
        Effectue un POST HTTP JSON.
        """

        final_payload = payload or self._raw_payload

        try:

            response = self._session.post(
                url,
                headers=self._headers,
                json=final_payload,
                timeout=self.timeout,
            )

            response.raise_for_status()

            return self._safe_json(response)

        except Timeout as exc:
            raise MySolensoException(
                "HTTP request timeout."
            ) from exc

        except RequestException as exc:
            raise MySolensoException(
                f"HTTP request error: {exc}"
            ) from exc

    @staticmethod
    def _safe_json(response: Response) -> dict:
        """
        Parse JSON sécurisé.
        """

        try:

            data = response.json()

            if not isinstance(data, dict):
                raise ValueError
            
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

            return data.get("data", {})

        except ValueError as exc:
            raise MySolensoException(
                "Invalid JSON response."
            ) from exc

    def __repr__(self) -> str:

        return (
            f"{self.__class__.__name__}("
            f"timeout={self.timeout}, "
            f"headers={list(self._headers.keys())})"
        )