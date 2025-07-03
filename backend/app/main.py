from fastapi import FastAPI
from app.api.api_v1.api import api_router
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base # Importez la classe Base
from app.db import base_class # Assure que les modèles sont "connus" de Base

# Importer les modèles pour qu'ils soient enregistrés avec Base.metadata
# Ceci est une façon de s'assurer qu'ils sont chargés.
from app.models import user, incident # Ajoutez d'autres modèles ici au fur et à mesure

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

def create_db_and_tables():
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully (if they didn't exist).")
    except Exception as e:
        print(f"Error creating database tables: {e}")

@app.on_event("startup")
async def on_startup():
    # Crée les tables de la base de données (si elles n'existent pas déjà)
    # C'est généralement ok pour le développement, mais pour la production,
    # vous utiliseriez Alembic ou un autre outil de migration.
    create_db_and_tables()
    # TODO: Créer un superutilisateur initial si nécessaire (voir étape suivante du plan)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"])
async def root():
    """
    Message de bienvenue de l'API.
    """
    return {"message": f"Welcome to {settings.PROJECT_NAME} API - Version 1"}
