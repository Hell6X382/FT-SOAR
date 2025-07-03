from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None # Changed from username to email to align with User model
    # sub: Optional[str] = None # 'sub' is often used for the subject (user identifier)
    # scopes: list[str] = [] # If using scopes for permissions
