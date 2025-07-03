from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Shared properties
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = Field(None, example="John Doe")

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="strongpassword123")

# Properties to receive via API on update
class UserUpdate(BaseModel): # Allow partial updates
    email: Optional[EmailStr] = Field(None, example="user@example.com")
    full_name: Optional[str] = Field(None, example="John Doe")
    password: Optional[str] = Field(None, min_length=8, example="newstrongpassword123")
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class UserInDBBase(UserBase):
    id: int = Field(..., example=1)

    class Config:
        from_attributes = True # For Pydantic V2 (replaces orm_mode)

# Additional properties to return via API
class User(UserInDBBase):
    pass

# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
