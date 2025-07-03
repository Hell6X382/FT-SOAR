from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_

from app.crud.base import CRUDBase
from app.models.incident import Incident, IncidentNote
from app.models.user import User # Pour type hinting
from app.schemas.incident import IncidentCreate, IncidentUpdate, IncidentNoteCreate, IncidentStatus, IncidentSeverity, IncidentNoteResponse
from app.schemas.user import User as UserSchema # Pour construire la réponse de note

class CRUDIncident(CRUDBase[Incident, IncidentCreate, IncidentUpdate]):

    # create() est hérité de CRUDBase et fonctionne pour IncidentCreate

    def get_multi_with_filtering(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "desc", # "asc" ou "desc"
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        search: Optional[str] = None
    ) -> List[Incident]:
        query = db.query(self.model)

        if status:
            query = query.filter(Incident.status == status)
        if severity:
            query = query.filter(Incident.severity == severity)
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    Incident.title.ilike(search_term),
                    Incident.description.ilike(search_term),
                    Incident.source.ilike(search_term) # Ajout de la source à la recherche
                )
            )

        # Gestion du tri via CRUDBase.get_multi ou ici spécifiquement
        default_sort_column = Incident.created_at
        if sort_by and hasattr(self.model, sort_by):
            column_to_sort = getattr(self.model, sort_by)
            if sort_order.lower() == "asc":
                query = query.order_by(asc(column_to_sort))
            else:
                query = query.order_by(desc(column_to_sort))
        else:
            query = query.order_by(desc(default_sort_column))

        return query.offset(skip).limit(limit).all()

    # --- Notes d'incident ---
    def add_note_to_incident(
        self,
        db: Session,
        *,
        incident_db_obj: Incident, # Attendre l'objet incident directement
        note_in: IncidentNoteCreate,
        user_db_obj: User # Attendre l'objet utilisateur directement
    ) -> IncidentNote:

        db_note = IncidentNote(
            content=note_in.content,
            incident_id=incident_db_obj.id,
            user_id=user_db_obj.id
            # created_at et updated_at sont gérés par la classe Base
        )
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        # db.refresh(incident_db_obj) # Pourrait être nécessaire si la relation n'est pas configurée avec back_populates ou si on veut voir la note immédiatement dans l'objet incident
        return db_note

    def get_notes_for_incident(
        self, db: Session, *, incident_id: int, skip: int = 0, limit: int = 100
    ) -> List[IncidentNote]:
        return db.query(IncidentNote)\
                 .filter(IncidentNote.incident_id == incident_id)\
                 .order_by(desc(IncidentNote.created_at))\
                 .offset(skip)\
                 .limit(limit)\
                 .all()

    # On pourrait vouloir une méthode pour obtenir une note spécifique
    def get_note(self, db: Session, note_id: int) -> Optional[IncidentNote]:
        return db.query(IncidentNote).filter(IncidentNote.id == note_id).first()

    # On pourrait vouloir une méthode pour mettre à jour une note (si permis)
    # def update_note(...)

    # On pourrait vouloir une méthode pour supprimer une note (si permis)
    # def remove_note(...)

incident = CRUDIncident(Incident)
# Pour les notes, il est plus simple de les gérer via CRUDIncident car elles sont très liées.
# Si IncidentNote devenait plus complexe, un CRUDIncidentNote(CRUDBase[IncidentNote, ...]) serait justifié.
