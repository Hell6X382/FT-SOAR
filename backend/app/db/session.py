from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Construction de l'URL de la base de données
SQLALCHEMY_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URL
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

logger.info(f"Connecting to database: {SQLALCHEMY_DATABASE_URL.split('@')[-1]}") # Log sans les crédentiels

engine_args = {}
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    engine_args["connect_args"] = {"check_same_thread": False}
    # Pourrait aussi ajouter poolclass=StaticPool pour SQLite en mémoire pour tests, mais pas pour dev général.
else:
    # Options de pooling pour PostgreSQL (ou autres DBs de production)
    engine_args["pool_size"] = 10 # Nombre de connexions à garder ouvertes dans le pool
    engine_args["max_overflow"] = 20 # Nombre de connexions supplémentaires qui peuvent être ouvertes au-delà de pool_size
    engine_args["pool_timeout"] = 30 # Secondes d'attente pour obtenir une connexion du pool avant de lever une erreur
    engine_args["pool_recycle"] = 1800 # Secondes après lesquelles une connexion est recyclée (évite les connexions périmées)


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    **engine_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dépendance FastAPI pour obtenir une session de base de données
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
