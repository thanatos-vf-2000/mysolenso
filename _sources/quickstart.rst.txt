Quick Start
===========

Installation
------------

.. code-block:: bash

   pip install mysolenso

Connect with a password
-----------------------

To recover your encrypted password, please use the project
`pwdsolenso <https://github.com/thanatos-vf-2000/pwdsolenso>`_

.. code-block:: python

   from mysolenso import MySolenso

   client = MySolenso(
       username="jdoe",
       password="encrypted_pass",  # server-side encrypted password
   )

   # User profile
   print(client.me.name)
   print(client.me.email)

   # Active station (first one by default)
   print(client.station.station_total)
   print(client.station.station_id)
   print(client.station.install_power)

Connect with an existing token
------------------------------

To recover an token, please use the project
`pwdsolenso <https://github.com/thanatos-vf-2000/pwdsolenso>`_

.. code-block:: python

   from mysolenso import MySolenso

   client = MySolenso(username="jdoe", token="eyJ...")

Real-time energy counters
-------------------------

.. code-block:: python

   print(client.stationcount.today_eq)    # kWh produced today
   print(client.stationcount.total_eq)    # kWh lifetime production
   print(client.stationcount.real_power)  # W current output
   print(client.stationcount.co2_emission_reduction)

Intra-day power curve
---------------------

.. code-block:: python

   result = client.powerbyday.get_data
   print(result["date"])               # "2026-05-15"
   print(result["values"]["10:00"])    # 2048.75  (W at 10:00)

   # Query a specific date
   client.powerbyday.set_day("2025-12-25")
   result = client.powerbyday.get_data

Day-of-year production history
-------------------------------

.. code-block:: python

   history = client.countbydayofyear.get_data
   print(history["2026-01-01"])   # Wh produced on that day
   print(history["2026-05-15"])   # 0.0 if not yet updated today

Error handling
--------------

.. code-block:: python

   from mysolenso import MySolenso
   from mysolenso.exceptions import (
       MySolensoAuthenticationException,
       MySolensoConnectionException,
       MySolensoException,
   )

   try:
       client = MySolenso(username="user", password="wrong")
   except MySolensoAuthenticationException as e:
       print(f"Invalid credentials: {e}")
   except MySolensoConnectionException as e:
       print(f"Missing parameters: {e}")
   except MySolensoException as e:
       print(f"General error: {e}")

Switch the active station
-------------------------

.. code-block:: python

   # List all stations
   for s in client.station.stations:
       print(s["id"], s["ak"])

   # Select the second station (1-based index)
   client.station.set_station(2)
   print(client.station.name)

   # Reload counters and history for the new station
   client.stationcount.set_station_count(client.station.station_id)
   client.countbydayofyear.set_station_id(client.station.station_id)
