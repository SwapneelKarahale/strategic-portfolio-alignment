import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://portfolio_app:portfolio_app@localhost:5432/portfolio_app"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    ANALYTICS_PROVIDER = os.environ.get("ANALYTICS_PROVIDER", "local")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL", "postgresql://portfolio_app:portfolio_app@localhost:5432/portfolio_app_test"
    )
