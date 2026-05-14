Quick Start
===========

Installation
------------

.. code-block:: bash

   pip install mysolenso

Connect with a password
-----------------------

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

If you already have a session token, you can use it directly to avoid
an authentication network call:

.. code-block:: python

   from mysolenso import MySolenso

   client = MySolenso(username="user@example.com", token="eyJ...")

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
