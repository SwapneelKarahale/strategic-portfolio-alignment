import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-key")
    # Some hosts hand out "postgres://", which SQLAlchemy 2 rejects; name the
    # psycopg2 driver explicitly so newer SQLAlchemy doesn't default to psycopg3.
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get(
            "DATABASE_URL", "postgresql://portfolio_app:portfolio_app@localhost:5432/portfolio_app"
        )
        .replace("postgres://", "postgresql://", 1)
        .replace("postgresql://", "postgresql+psycopg2://", 1)
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = [
        origin.strip().rstrip("/")
        for origin in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    ANALYTICS_PROVIDER = os.environ.get("ANALYTICS_PROVIDER", "local")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL", "postgresql://portfolio_app:portfolio_app@localhost:5432/portfolio_app_test"
    )
