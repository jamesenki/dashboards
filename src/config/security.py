"""
Security configurations for IoTSphere platform.

This module contains security-related configurations including JWT settings,
cookie security, and other authentication/authorization parameters.
"""
import os
from datetime import timedelta

# JWT Settings
SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY", "iotsphere_development_key_do_not_use_in_production"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Cookie Settings
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
COOKIE_HTTPONLY = True
COOKIE_SAMESITE = "lax"  # Options: "lax", "strict", or "none"

# CORS Settings
CORS_ALLOW_ORIGINS = os.environ.get(
    "CORS_ALLOW_ORIGINS", "http://localhost:8000,http://localhost:5000"
).split(",")

CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

CORS_ALLOW_HEADERS = ["Content-Type", "Authorization", "Accept"]

# Password Settings
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGITS = True
PASSWORD_REQUIRE_SPECIAL = True

# Session Settings
SESSION_LIFETIME = timedelta(hours=12)

# WebSocket Authentication
WEBSOCKET_AUTH_REQUIRED = True
WEBSOCKET_AUTH_COOKIE_NAME = "iotsphere_auth"
WEBSOCKET_AUTH_HEADER_NAME = "X-IoTSphere-Auth"

# Rate Limiting
RATE_LIMIT_PER_MINUTE = 100  # Default rate limit per minute per client
