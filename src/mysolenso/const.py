"""Constants for MySolenso library for Python."""

DEFAULT_TIMEOUT = 10  # secondes

BASE_URL_SOLENSO   = "https://monitor.solenso.net/platform/"

#Login
API_AUTH_LOGIN = BASE_URL_SOLENSO + "api/gateway/iam/auth_login"

#My information
API_USER_ME = BASE_URL_SOLENSO + "api/gateway/iam/fun_api_1_user_me"

#My Station:
API_STATION_ME = BASE_URL_SOLENSO + "api/gateway/pvm/station_select_by_page"