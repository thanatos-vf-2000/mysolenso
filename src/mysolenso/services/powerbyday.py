from __future__ import annotations

import logging
from typing import Union
from datetime import datetime,timedelta
import re
import struct

from ..post import MySolensoPost
from ..const import API_POWER_BY_DAY
from ..exceptions import MySolensoException

_LOG = logging.getLogger(__name__)


class MySolensoPowerByDay:
    
    def __init__(self, parent) -> None:
        self.parent = parent
        
        # Guard: station_id must be resolved before instantiation
        if self.parent.station.station_id is None:
            msg = f"{self.__class__.__name__} station_id is None."
            _LOG.warning(msg)
            raise MySolensoException(msg)

        self._station_id = self.parent.station.station_id
        
        self._day = None
        now = datetime.now()
        if now.hour < 1:
            yesterday = now - timedelta(days=1)
            self._day = yesterday.strftime("%Y-%m-%d")
        else:
            self._day = now.strftime("%Y-%m-%d")
        
        self._get_power_by_day()
    
    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------

    def _get_power_by_day(self) -> None:
        try:
            self._client = MySolensoPost()
            self._client.set_headers(self.parent.auth.get_auth_headers_hoymiles())
            self._client.set_raw_payload({"sid":self._station_id ,"date":self._day})
            response = self._client.poststr(API_POWER_BY_DAY)

            # ---------------------------------------------------
            # Extraction des heures HH:MM
            # ---------------------------------------------------
            times = re.findall(rb'(\d{2}:\d{2})', response)
            times = [t.decode() for t in times]

            # ---------------------------------------------------
            # Extraction de la date
            # ---------------------------------------------------
            date_match = re.search(rb'(\d{4}-\d{2}-\d{2})', response)
            date_value = date_match.group(1).decode() if date_match else None

            # ---------------------------------------------------
            # Extraction des float grid_power
            # ---------------------------------------------------
            # Position du mot "grid_power"
            marker = b'grid_power'

            idx = response.find(marker)

            if idx == -1:
                raise Exception("grid_power introuvable")

            # ---------------------------------------------------
            # Début des float protobuf
            # ---------------------------------------------------
            # après:
            # grid_power\x12\x90\x02
            start = idx + len(marker) + 3

            # ---------------------------------------------------
            # Fin des floats avant la date
            # ---------------------------------------------------
            date_marker = b'\x1a\n'

            end = response.find(date_marker)

            if end == -1:
                end = len(response)

            binary_part = response[start:end]

            # ---------------------------------------------------
            # Lecture float32 little endian
            # ---------------------------------------------------
            floats = []

            for i in range(0, len(binary_part), 4):

                chunk = binary_part[i:i+4]

                if len(chunk) != 4:
                    continue

                value = struct.unpack('<f', chunk)[0]

                floats.append(round(value, 2))

            # ---------------------------------------------------
            # Association heure -> valeur
            # ---------------------------------------------------
            values = {}

            for t, v in zip(times, floats):
                values[t] = v

            # ---------------------------------------------------
            # Structure finale
            # ---------------------------------------------------
            self._result = {
                "metric": "grid_power",
                "date": date_value,
                "values": values
            }
            
            

        except Exception as e:
            raise MySolensoException(
                "Invalid or corrupted JSON response."
            ) from e
    
    def set_station_id(self, id: int, refresh: bool = True) -> None:
        stations = self.parent.station.stations
        exists = any(station.get("id") == id for station in stations)

        if not exists:
            msg = (
                f"{self.__class__.__name__} - set_station_find: "
                f"station {id} not found."
            )
            _LOG.warning(msg)
            raise MySolensoException(msg)

        self._station_id = id
        
        if refresh:
            self._get_power_by_day()
        
    def set_day(self, day: str, refresh: bool = True) -> None:
        try:
            # Vérifie longueur exacte
            if len(day) != 10:
                raise ValueError("Format invalide")

            # Vérifie format YYYY-MM-DD
            date_obj = datetime.strptime(day, "%Y-%m-%d").date()

            # Bornes autorisées
            min_date = datetime(1900, 1, 1).date()
            max_date = datetime.now().date()

            # Vérifie plage
            if not (min_date <= date_obj <= max_date):
                msg = (
                    f"{self.__class__.__name__} - set_day: "
                    f"Date outside the allowed range {min_date} <= {date_obj} <= {max_date}."
                )
                _LOG.warning(msg)
                raise MySolensoException(msg)
            
            self._day = day
            if refresh:
                self._get_power_by_day()

        except ValueError as e:
            msg = (
                f"{self.__class__.__name__} - set_day: "
                f"day {day} not valid."
            )
            _LOG.warning(msg)
            raise MySolensoException(msg)
    
    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def get_data(self) -> dict:
        return self._result