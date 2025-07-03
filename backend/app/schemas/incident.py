from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class IncidentStatus(str, Enum):
    OPEN = "Ouvert"
    IN_PROGRESS = "En cours"
    RESOLVED = "Résolu"
    CLOSED = "Fermé"

class IncidentSeverity(str, Enum):
    LOW = "Faible"
    MEDIUM = "Moyenne"
    HIGH = "Haute"
    CRITICAL = "Critique"

# --- Incident Notes ---
class IncidentNoteBase(BaseModel):
    content: str = Field(..., min_length=1, example="Initial analysis of the alert.")

class IncidentNoteCreate(IncidentNoteBase):
    pass

class IncidentNoteResponse(IncidentNoteBase): # Schema for API response
    id: int
    created_at: datetime
    user_email: EmailStr # Assuming we'll link notes to users by email for simplicity or display

    class Config:
        from_attributes = True

# --- Incident ---
class IncidentBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, example="Suspicious Login Attempt Detected")
    description: Optional[str] = Field(None, example="A suspicious login attempt was detected from IP 192.168.1.100.")
    status: IncidentStatus = Field(default=IncidentStatus.OPEN, example=IncidentStatus.OPEN)
    severity: IncidentSeverity = Field(default=IncidentSeverity.MEDIUM, example=IncidentSeverity.MEDIUM)
    source: Optional[str] = Field(None, example="SIEM Alert ID: 12345")
    # tags: Optional[List[str]] = Field(default_factory=list, example=["phishing", "internal"])

# Properties to receive on incident creation
class IncidentCreate(IncidentBase):
    pass

# Properties to receive on incident update (all optional for PATCH)
class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    status: Optional[IncidentStatus] = None
    severity: Optional[IncidentSeverity] = None
    source: Optional[str] = None
    # tags: Optional[List[str]] = None

# Properties shared by models stored in DB
class IncidentInDBBase(IncidentBase):
    id: int = Field(..., example=101)
    created_at: datetime
    updated_at: datetime
    # owner_id: Optional[int] = None # Future: assign to a user

    class Config:
        from_attributes = True

# Properties to return to client (API response model)
class IncidentResponse(IncidentInDBBase):
    notes: List[IncidentNoteResponse] = Field(default_factory=list)
    # Could include more details here, like linked IOCs, affected entities if modeled

# Properties stored in DB (can be same as IncidentInDBBase if no other DB-specific fields)
class IncidentInDB(IncidentInDBBase):
    pass
