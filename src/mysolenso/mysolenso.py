
from __future__ import annotations
import logging
from typing import Optional

from .auth import MySolensoAuth
from .services.me import MySolensoMe
from .services.station import MySolensoStation

_LOG = logging.getLogger(__name__)

class MySolenso:
    def __init__(
        self, 
        username: str,
        password: Optional[str] = None,
        token: Optional[str] = None)-> None:
        self.username = username
        self.password = password
        self.token = token

        # Sous-modules
        self.auth    = MySolensoAuth(
            username=self.username, 
            password=self.password,
            token=self.token)
        self.me      = MySolensoMe(self)
        self.station = MySolensoStation(self)