"""Application configuration.

Reads sensitive values from environment variables where available and
falls back to sane local-development defaults.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base Flask configuration."""

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    _default_db = "sqlite:////tmp/database.db" if os.environ.get("VERCEL") else f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
    _db_url = os.environ.get("DATABASE_URL", _default_db)
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI: str = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    WTF_CSRF_ENABLED: bool = True

    # Pagination
    INCIDENTS_PER_PAGE: int = 10

    # Domain constants shared across models/forms/templates
    SEVERITIES = ["low", "medium", "high", "critical"]
    STATUSES = ["open", "investigating", "resolved"]
