"""
config.py
---------
Centralized configuration for the entire application.

Design decision: Every other module reads settings through this single
Config class instead of calling os.getenv() directly. This means:
  1. All configuration is documented and discoverable in one place.
  2. Switching environments (dev/test/prod) requires no code changes.
  3. Misconfigured/missing env vars fail loudly and early (at import time)
     rather than causing silent bugs deep inside the app.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load variables from .env into the process environment.
# This must happen before Config reads anything.
load_dotenv()


def _get_env(key: str, default: str = None, required: bool = False) -> str:
    """
    Small helper to fetch an environment variable with optional
    'required' enforcement. Fails fast with a clear error message
    instead of letting a None propagate silently into, e.g., a
    database connection string.
    """
    value = os.getenv(key, default)
    if required and value is None:
        raise EnvironmentError(
            f"Missing required environment variable: '{key}'. "
            f"Did you copy .env.example to .env and fill it in?"
        )
    return value


@dataclass(frozen=True)
class DatabaseConfig:
    """Groups all MySQL connection settings together."""
    host: str = _get_env("DB_HOST", "localhost")
    port: int = int(_get_env("DB_PORT", "3306"))
    name: str = _get_env("DB_NAME", "rpm_system")
    user: str = _get_env("DB_USER", "root")
    password: str = _get_env("DB_PASSWORD", required=True)


@dataclass(frozen=True)
class SecurityConfig:
    """Groups all authentication/security-related settings."""
    secret_key: str = _get_env("APP_SECRET_KEY", required=True)
    bcrypt_rounds: int = int(_get_env("BCRYPT_ROUNDS", "12"))
    session_expiry_minutes: int = int(_get_env("SESSION_EXPIRY_MINUTES", "60"))


@dataclass(frozen=True)
class RiskThresholds:
    """
    Risk classification cut-points used by the ML risk_engine to convert
    a raw probability (0.0 - 1.0) into a clinical risk_level label.
    Kept configurable (not hardcoded in ML code) so thresholds can be
    tuned by a clinician/supervisor without touching model code.
    """
    medium: float = float(_get_env("RISK_THRESHOLD_MEDIUM", "0.4"))
    high: float = float(_get_env("RISK_THRESHOLD_HIGH", "0.7"))
    critical: float = float(_get_env("RISK_THRESHOLD_CRITICAL", "0.9"))


class Config:
    """
    Top-level application configuration.
    Usage:
        from app.core.config import Config
        Config.DB.host
        Config.SECURITY.secret_key
    """
    APP_ENV: str = _get_env("APP_ENV", "development")
    DB: DatabaseConfig = DatabaseConfig()
    SECURITY: SecurityConfig = SecurityConfig()
    RISK: RiskThresholds = RiskThresholds()

    @classmethod
    def is_production(cls) -> bool:
        return cls.APP_ENV.lower() == "production"
