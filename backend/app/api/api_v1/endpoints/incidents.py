from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import EmailStr # Pour le type hint de user_email dans IncidentNoteResponse

from app import crud, models, schemas # schemas contient IncidentResponse, IncidentCreate, etc.
from app.api import deps # Contient get_db, get_current_active_user
from app.schemas.incident import IncidentStatus, IncidentSeverity # Pour les paramètres de Query
# Le schéma IncidentNoteResponse est dans schemas.incident

router = APIRouter()

@router.post("/", response_model=schemas.IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    *,
    db: Session = Depends(deps.get_db),
    incident_in: schemas.IncidentCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new incident.
    The incident object returned will include an empty list of notes by default.
    The `creator_id` or `owner_id` is not explicitly set here but could be added
    to `IncidentCreate` or handled in `crud.incident.create`.
    """
    new_incident = crud.incident.create(db=db, obj_in=incident_in)
    # `lazy="selectin"` sur la relation `notes` du modèle `Incident` devrait charger les notes
    # (qui seront vides au début) lorsque Pydantic accède à l'attribut `notes`.
    return new_incident

@router.get("/", response_model=List[schemas.IncidentResponse])
async def read_incidents(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0, description="Number of items to skip."),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of items to return."),
    sort_by: Optional[str] = Query(None, description="Sort by field (e.g., 'created_at', 'severity', 'status', 'title'). Default: 'created_at'"),
    sort_order: Optional[str] = Query("desc", description="Sort order ('asc' or 'desc'). Default: 'desc'"),
    status_filter: Optional[IncidentStatus] = Query(None, alias="status", description="Filter by incident status."),
    severity_filter: Optional[IncidentSeverity] = Query(None, alias="severity", description="Filter by incident severity."),
    search_filter: Optional[str] = Query(None, alias="search", min_length=2, description="Search term for title, description, and source."),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve incidents with filtering, sorting, and pagination.
    """
    incidents = crud.incident.get_multi_with_filtering(
        db,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        status=status_filter,
        severity=severity_filter,
        search=search_filter
    )
    return incidents

@router.get("/{incident_id}", response_model=schemas.IncidentResponse)
async def read_incident(
    *,
    db: Session = Depends(deps.get_db),
    incident_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get incident by ID. Includes associated notes.
    """
    incident = crud.incident.get(db=db, id=incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    # `lazy="selectin"` sur la relation `notes` et `lazy="joined"` sur `IncidentNote.user`
    # devraient permettre à Pydantic de construire `IncidentResponse` correctement.
    return incident

@router.put("/{incident_id}", response_model=schemas.IncidentResponse)
async def update_incident(
    *,
    db: Session = Depends(deps.get_db),
    incident_id: int,
    incident_in: schemas.IncidentUpdate, # Utilise le schéma de mise à jour partiel
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an incident. Allows partial updates.
    """
    incident_db_obj = crud.incident.get(db=db, id=incident_id)
    if not incident_db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    # TODO: Ajouter des vérifications de permission si nécessaire (ex: seul le créateur ou un admin peut modifier)

    updated_incident = crud.incident.update(db=db, db_obj=incident_db_obj, obj_in=incident_in)
    return updated_incident

@router.delete("/{incident_id}", response_model=schemas.Msg)
async def delete_incident(
    *,
    db: Session = Depends(deps.get_db),
    incident_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser), # Seuls les superusers peuvent supprimer
) -> Any:
    """
    Delete an incident. (Requires superuser privileges)
    """
    incident_to_delete = crud.incident.get(db=db, id=incident_id)
    if not incident_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    crud.incident.remove(db=db, id=incident_id)
    return schemas.Msg(message=f"Incident with ID {incident_id} deleted successfully.")


# --- Endpoints pour les Notes d'Incident ---

@router.post("/{incident_id}/notes/", response_model=schemas.IncidentNoteResponse, status_code=status.HTTP_201_CREATED)
async def add_note_to_incident_endpoint(
    *,
    db: Session = Depends(deps.get_db),
    incident_id: int,
    note_in: schemas.IncidentNoteCreate,
    current_user: models.User = Depends(deps.get_current_active_user), # L'utilisateur qui ajoute la note
) -> Any:
    """
    Add a new note to an existing incident.
    The user adding the note is the currently authenticated user.
    """
    incident_db_obj = crud.incident.get(db=db, id=incident_id)
    if not incident_db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found to add note to.")

    # current_user est l'objet User model complet grâce à deps.get_current_active_user
    new_note = crud.incident.add_note_to_incident(
        db=db, incident_db_obj=incident_db_obj, note_in=note_in, user_db_obj=current_user
    )

    # Pydantic V2 avec `from_attributes=True` dans IncidentNoteResponse:
    # Le schéma attend: id, created_at, content, user_email.
    # new_note.id, new_note.created_at, new_note.content sont directs.
    # Pour user_email, Pydantic va essayer d'accéder à new_note.user.email
    # car la relation `user` sur `IncidentNote` est `lazy="joined"`.
    # Assurez-vous que `schemas.incident.IncidentNoteResponse` est bien:
    # class IncidentNoteResponse(IncidentNoteBase):
    #   id: int
    #   created_at: datetime
    #   user_email: EmailStr  <-- Ceci doit être mappé depuis note.user.email
    #   class Config: from_attributes = True

    # Pour que cela fonctionne, il faut que le schéma Pydantic `IncidentNoteResponse`
    # soit capable de résoudre `user_email` à partir de l'objet `IncidentNote` et de sa relation `user`.
    # Si `IncidentNoteResponse` a un champ `user: UserSchema`, Pydantic le mapperait.
    # S'il a `user_email: EmailStr`, il faut que l'objet `IncidentNote` ait un attribut `user_email`
    # ou une propriété, OU que Pydantic soit assez intelligent pour faire `note.user.email`.
    # Avec `from_attributes = True` et `lazy="joined"`, Pydantic *devrait* pouvoir accéder à `note.user.email`.

    # Alternative si Pydantic ne résout pas `user_email` automatiquement :
    # return schemas.IncidentNoteResponse(
    #     id=new_note.id,
    #     created_at=new_note.created_at,
    #     content=new_note.content,
    #     user_email=new_note.user.email # Accès explicite
    # )
    # Mais la conversion automatique est préférable.
    return new_note


@router.get("/{incident_id}/notes/", response_model=List[schemas.IncidentNoteResponse])
async def get_incident_notes_endpoint(
    *,
    db: Session = Depends(deps.get_db),
    incident_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve notes for a specific incident.
    """
    incident_db_obj = crud.incident.get(db=db, id=incident_id) # Vérifier que l'incident existe
    if not incident_db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    notes = crud.incident.get_notes_for_incident(db=db, incident_id=incident_id, skip=skip, limit=limit)
    # Encore une fois, la conversion en List[schemas.IncidentNoteResponse] dépend de la configuration
    # de `from_attributes` et du chargement de la relation `user` (qui est `lazy="joined"`).
    return notes
