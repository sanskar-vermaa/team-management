import logging
import os

DEV_SECRET_KEY = "dev-only-secret-key-change-me"  # noqa: S105 - placeholder, rejected in production
log = logging.getLogger(__name__)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or DEV_SECRET_KEY
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_MB", "2")) * 1024 * 1024
    WTF_CSRF_TIME_LIMIT = None  # tokens live as long as the session
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("APP_ENV") == "production"
    APP_ENV = os.environ.get("APP_ENV", "development")


def check_config(config: dict) -> None:
    """Refuse to run in production with the public development key."""
    if config.get("SECRET_KEY") == DEV_SECRET_KEY:
        if config.get("APP_ENV") == "production":
            raise RuntimeError("SECRET_KEY must be set when APP_ENV=production")
        log.warning("SECRET_KEY is not set; using the development key")
