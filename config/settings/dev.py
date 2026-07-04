from .base import *

DEBUG = True

ALLOWED_HOSTS = [
    "localhost", 
    "127.0.0.1"
]


DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE"),
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT"),
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": (
                "SET sql_mode='STRICT_TRANS_TABLES,"
                "NO_ZERO_DATE,NO_ZERO_IN_DATE,"
                "ERROR_FOR_DIVISION_BY_ZERO'"
            ),
        },
    }
}


SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False