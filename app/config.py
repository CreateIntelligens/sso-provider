import os
from datetime import timedelta
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables from .env if present
load_dotenv()


class Settings:
    # Cookie settings (optional)
    COOKIE_DOMAIN: str | None = os.getenv("COOKIE_DOMAIN")  # e.g. .test.com
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "true").lower() == "true"
    COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "Lax")  # "Lax" | "None" | "Strict"
    COOKIE_HTTPONLY: bool = os.getenv("COOKIE_HTTPONLY", "false").lower() == "true"

    # Database
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "w23452345")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "sso_provider")

    # Prefer explicit DATABASE_URL if provided; otherwise build it safely (URL-encode creds)
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI: str = DATABASE_URL
    else:
        _DB_USER_ENC = quote_plus(DB_USER)
        _DB_PASSWORD_ENC = quote_plus(DB_PASSWORD)
        SQLALCHEMY_DATABASE_URI: str = (
            f"mysql+pymysql://{_DB_USER_ENC}:{_DB_PASSWORD_ENC}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

    # App secrets
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "dev-session-secret-change-me")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me")  # HS256 for PoC
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRES_DELTA: timedelta = timedelta(minutes=int(os.getenv("JWT_EXPIRES_MINUTES", "15")))

    # UI
    SITE_NAME: str = os.getenv("SITE_NAME", "SSO Provider")

settings = Settings()
