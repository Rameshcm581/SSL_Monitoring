import os
from typing import Optional


class ConfigError(RuntimeError):
    """Raised when a required environment variable is missing."""


def _require(key: str) -> str:
    value = os.getenv(key)
    if value is None or value == "":
        raise ConfigError(f"Required environment variable '{key}' is not set.")
    return value


def _optional(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(key, default)


class BaseConfig:
    SECRET_KEY: str = _require("SECRET_KEY")
    ALGORITHM: str = _require("JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(_require("ACCESS_TOKEN_EXPIRE_MINUTES"))

    _RAW_ORIGINS: str = _require("ALLOWED_ORIGINS")
    ALLOWED_ORIGINS: list = [o.strip() for o in _RAW_ORIGINS.split(",") if o.strip()]

    DB_URI: str = _require("DB_URI")

    SENDGRID_API_KEY: str = _require("SENDGRID_API_KEY")
    ALERT_FROM_EMAIL: str = _require("ALERT_FROM_EMAIL")

    STRIPE_SECRET_KEY: str = _require("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: str = _require("STRIPE_WEBHOOK_SECRET")
    STRIPE_PRICE_ID: str = _require("STRIPE_PRICE_ID")

    CHECK_INTERVAL_MINUTES: int = int(_optional("CHECK_INTERVAL_MINUTES", "5"))
    SSL_CHECK_INTERVAL_HOURS: int = int(_optional("SSL_CHECK_INTERVAL_HOURS", "24"))
