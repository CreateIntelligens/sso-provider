import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


class Settings:
    # Cookie settings
    COOKIE_DOMAIN: str | None = os.getenv("COOKIE_DOMAIN")  # e.g. .test.com
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "true").lower() == "true"
    COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "Lax")  # "Lax" | "None" | "Strict"
    COOKIE_HTTPONLY: bool = os.getenv("COOKIE_HTTPONLY", "false").lower() == "true"  # set false to allow frontend JS to read

    # Database
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "w23452345")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "sso_provider")
    SQLALCHEMY_DATABASE_URI: str = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # App secrets
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "dev-session-secret-change-me")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me")  # HS256 for PoC
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRES_DELTA: timedelta = timedelta(minutes=int(os.getenv("JWT_EXPIRES_MINUTES", "15")))

    # UI
    SITE_NAME: str = os.getenv("SITE_NAME", "SSO Provider")

settings = Settings()
