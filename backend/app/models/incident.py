from sqlalchemy import Column, String, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.schemas.incident import IncidentStatus, IncidentSeverity # Pydantic Enums for default values

# Important: Le nom de l'enum SQL doit être unique dans la base de données.
# Si vous avez plusieurs enums avec les mêmes valeurs (ex: status pour différents objets),
# donnez-leur des noms distincts dans la DB.
# ex: name="incident_status_enum_v1"

class Incident(Base):
    # __tablename__ est automatiquement généré comme "incidents"

    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Utilisation de SAEnum pour créer un type ENUM dans la base de données (si supporté, sinon VARCHAR)
    # Les valeurs de l'enum Pydantic sont utilisées pour les valeurs par défaut et la validation applicative.
    status = Column(SAEnum(IncidentStatus, name="incident_status_type", create_constraint=True, validate_strings=True),
                    nullable=False,
                    default=IncidentStatus.OPEN,
                    server_default=IncidentStatus.OPEN.value)

    severity = Column(SAEnum(IncidentSeverity, name="incident_severity_type", create_constraint=True, validate_strings=True),
                      nullable=False,
                      default=IncidentSeverity.MEDIUM,
                      server_default=IncidentSeverity.MEDIUM.value)

    source = Column(String(255), nullable=True)

    # Exemple: Lier un incident à un créateur (utilisateur)
    # creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # creator = relationship("User", back_populates="created_incidents")

    # Relation avec IncidentNote
    # cascade="all, delete-orphan" signifie que si un Incident est supprimé, ses notes associées le sont aussi.
    notes = relationship("IncidentNote", back_populates="incident", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self):
        return f"<Incident(id={self.id}, title='{self.title}', status='{self.status.value}')>"

class IncidentNote(Base):
    # __tablename__ est automatiquement généré comme "incident_notes"

    content = Column(Text, nullable=False)

    incident_id = Column(Integer, ForeignKey("incidents.id", name="fk_incidentnote_incident_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", name="fk_incidentnote_user_id"), nullable=True) # Qui a écrit la note, nullable si système

    # Relations
    incident = relationship("Incident", back_populates="notes")
    user = relationship("User", back_populates="incident_notes", lazy="joined") # `lazy="joined"` pour charger l'utilisateur avec la note

    def __repr__(self):
        return f"<IncidentNote(id={self.id}, incident_id={self.incident_id}, user_id={self.user_id})>"
