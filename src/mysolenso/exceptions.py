"""Exceptions for the MySolenso library.

This module defines the complete exception hierarchy raised by the library.
All exceptions inherit from :class:`MySolensoException`, allowing unified
error handling with a single ``except`` block.

Hierarchy::

    Exception
    └── MySolensoException
        ├── MySolensoConnectionException
        └── MySolensoAuthenticationException

Example:
    Handling exceptions in your code::

        from mysolenso.exceptions import (
            MySolensoException,
            MySolensoAuthenticationException,
            MySolensoConnectionException,
        )

        try:
            client = MySolensoAuth(username="user", password="pass")
        except MySolensoAuthenticationException as e:
            print(f"Invalid credentials: {e}")
        except MySolensoConnectionException as e:
            print(f"Network issue: {e}")
        except MySolensoException as e:
            print(f"General MySolenso error: {e}")
"""


class MySolensoException(Exception):
    """Base exception for the MySolenso library.

    All MySolenso-specific exceptions inherit from this class.
    Use it to catch any error raised by the library in a single
    ``except`` block.

    Example:
        ::

            try:
                ...
            except MySolensoException as e:
                print(e)
    """


class MySolensoConnectionException(MySolensoException):
    """Connection or parameter validation error.

    Raised when the provided arguments are invalid (empty username,
    missing both password and token, etc.) or when a network issue
    occurs before the request is sent.

    Example:
        ::

            # Empty username → MySolensoConnectionException
            MySolensoAuth(username="", token="abc")

            # Neither password nor token → MySolensoConnectionException
            MySolensoAuth(username="admin")
    """


class MySolensoAuthenticationException(MySolensoException):
    """Authentication error from the Solenso API.

    Raised when the API returns an error status, an unexpected message,
    or when the token is missing from the response.

    Example:
        ::

            # Wrong password → MySolensoAuthenticationException
            MySolensoAuth(username="admin", password="wrong")

            # Calling get_auth_headers without a valid token
            client.disconnect()
            client.get_auth_headers_hoymiles()  # raises this exception
    """
