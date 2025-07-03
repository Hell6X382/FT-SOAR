from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "CyberSecurity Incident Orchestrator"
    API_V1_STR: str = "/api/v1"

    # Database (SQLite for now, PostgreSQL for prod)
    # Pour PostgreSQL: postgresql://user:password@host:port/dbname
    SQLALCHEMY_DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./cyber_orchestrator.db")

    # JWT Settings
    # IMPORTANT: Change this in a real environment and use environment variables!
    # openssl rand -hex 32
    SECRET_KEY: str = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ALGORITHM: str = "HS256"
    # Durée de validité du token d'accès (en minutes)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 heures

    # First superuser
    FIRST_SUPERUSER_EMAIL: str = os.getenv("FIRST_SUPERUSER_EMAIL", "admin@example.com")
    FIRST_SUPERUSER_PASSWORD: str = os.getenv("FIRST_SUPERUSER_PASSWORD", "adminpassword")


    class Config:
        case_sensitive = True
        # Pour charger les variables d'environnement à partir d'un fichier .env (nécessite python-dotenv)
        # env_file = ".env"

settings = Settings()
