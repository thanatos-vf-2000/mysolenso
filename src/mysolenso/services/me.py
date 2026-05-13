from __future__ import annotations
import logging
from ..post import MySolensoPost

from ..const import API_USER_ME
from ..exceptions import MySolensoException

_LOG = logging.getLogger(__name__)

class MySolensoMe:
    
    def __init__(self, parent):
        self.parent = parent
        self._get_user_me()
        
    
    def _get_user_me(self):
        try:
                
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_solenso())
            response = self._client.post(API_USER_ME)
            
            self._username  = str(response.get("user_name", "")).strip()
            self._name      = str(response.get("name", "")).strip()
            self._phone     = str(response.get("phone", "")).strip()
            self._email     = str(response.get("email", "")).strip()
            self._role_ids  = str(response.get("role_ids", "")).strip()
            self._roles_name = str(response.get("roles", [{}])[0].get("name", "")).strip()
            self._group_name = str(response.get("group", {}).get("name", "")).strip()
            self._all_data   = response
            
        except Exception as e:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from e
    
    
    @property
    def username(self) -> str:
        return self._username
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def phone(self) -> str:
        return self._phone
    
    @property
    def email(self) -> str:
        return self._email
    
    @property
    def role_ids(self) -> str:
        return self._role_ids
    
    @property
    def roles_name(self) -> str:
        return self._roles_name
    
    @property
    def group_name(self) -> str:
        return self._group_name
    
    @property
    def all_data(self) -> dict:
        return self._all_data