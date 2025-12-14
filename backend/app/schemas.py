# Replace your entire schemas.py with this:

from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from uuid import UUID

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    name: str
    picture: Optional[str] = None

class UserOut(UserBase):
    id: str # Google ID
    class Config:
        from_attributes = True

# --- Helper Schema for ProjectOut ---
# We use this to avoid circular dependency (Project -> Request -> Project)
class CollabRequestSimple(BaseModel):
    id: UUID
    status: str
    sender_id: str
    sender: Optional[UserOut]
    created_at: datetime
    class Config:
        from_attributes = True

# --- Project Schemas ---
class ProjectCreate(BaseModel):
    title: str
    abstract: Optional[str] = None

class ProjectOut(BaseModel):
    id: UUID
    title: str
    file_url: Optional[str] = None
    abstract: Optional[str] = None
    topics: List[str] = []
    views_count: int
    created_at: datetime
    user: Optional[UserOut]
    
    # NEW FIELD: This sends the list to the frontend
    collab_requests: List[CollabRequestSimple] = [] 
    
    class Config:
        from_attributes = True

# --- Collab Schemas ---
class CollabRequestOut(BaseModel):
    id: UUID
    status: str
    sender: UserOut
    project: ProjectOut
    created_at: datetime
    class Config:
        from_attributes = True

# --- Chat Schemas ---
class ChatMessageOut(BaseModel):
    id: UUID
    content: str
    is_ai: bool
    sender_id: str
    created_at: datetime
    sender: Optional[UserOut]
    class Config:
        from_attributes = True