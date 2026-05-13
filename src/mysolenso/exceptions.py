"""Exceptions for the MySolenso library."""


class MySolensoException(Exception):
    """Base exception of the MySolenso library."""

class MySolensoConnectionException(MySolensoException):
    """An error occurred in the connection with the device."""

class MySolensoAuthenticationException(MySolensoException):
    """An error occurred in the authentication process."""