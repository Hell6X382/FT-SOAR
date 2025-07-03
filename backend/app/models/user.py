from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base # Importer notre classe Base personnalisée

class User(Base):
    # __tablename__ est automatiquement généré comme "users" par la classe Base

    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False) # Augmenté la taille pour les hash
    full_name = Column(String(255), index=True, nullable=True)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)

    # Relations
    # Incidents créés par cet utilisateur (si on implémente un créateur pour les incidents)
    # created_incidents = relationship("Incident", back_populates="creator", foreign_keys="[Incident.creator_id]")

    # Notes d'incident écrites par cet utilisateur
    incident_notes = relationship("IncidentNote", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', is_superuser={self.is_superuser})>"
