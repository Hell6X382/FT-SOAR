from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, incidents # Décommenter/ajouter incidents
# Importer les autres futurs routers ici au fur et à mesure
# from app.api.api_v1.endpoints import playbooks, connections, dashboard

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
# api_router.include_router(playbooks.router, prefix="/playbooks", tags=["Playbooks"])
# api_router.include_router(connections.router, prefix="/connections", tags=["Connections"])
# api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
