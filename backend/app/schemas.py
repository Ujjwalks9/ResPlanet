from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any
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
    user: Optional[UserOut] # Relationship
    
    class Config:
        from_attributes = True

# --- Collab Schemas ---
class CollabRequestOut(BaseModel):
    id: UUID
    status: str
    sender: UserOut
    project: ProjectOut
    created_at: datetime

# --- Chat Schemas ---
class ChatMessageOut(BaseModel):
    id: UUID
    content: str
    is_ai: bool
    sender_id: str
    created_at: datetime
    sender: Optional[UserOut]