"""
SecureAssess — Application Configuration.

Loads settings from environment variables with sensible defaults.
Never hardcode secrets here — use .env files.
"""

import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration shared by all environments."""

    # --- Flask ---
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_ME")

    # --- MongoDB ---
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "secureassess")

    # --- JWT ---
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_ME")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "900"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "604800"))
    )
    JWT_ALGORITHM = "HS256"
    JWT_ERROR_MESSAGE_KEY = "message"

    # --- CORS ---
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    # --- Rate Limiting ---
    RATE_LIMIT_AUTH = os.getenv("RATE_LIMIT_AUTH", "5/minute")
    RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "30/minute")

    # --- Security ---
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB payload limit

    # --- Admin Seed ---
    ADMIN_NAME = os.getenv("ADMIN_NAME", "Admin")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@secureassess.local")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@1234")


class DevelopmentConfig(Config):
    """Development-specific overrides."""

    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production-specific overrides."""

    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing-specific overrides — uses a separate database."""

    DEBUG = True
    TESTING = True
    MONGO_DB_NAME = "secureassess_test"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=300)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=600)
    RATE_LIMIT_AUTH = "100/minute"
    RATE_LIMIT_DEFAULT = "200/minute"


# Map environment names to config classes
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config():
    """Return the config class for the current FLASK_ENV."""
    env = os.getenv("FLASK_ENV", "development")
    return config_by_name.get(env, DevelopmentConfig)
