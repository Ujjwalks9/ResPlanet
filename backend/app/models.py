import uuid
from datetime import datetime
from sqlalchemy import Enum as SQLEnum
import enum
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True)
    name = Column(String)

class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String)
    file_url = Column(String)
    abstract = Column(Text, nullable=True)
    topics = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    is_processed = Column(Boolean, default=False)

class Embedding(Base):
    __tablename__ = "embeddings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    content = Column(Text)
    
    # CHANGED: 1536 -> 768 for Gemini Embeddings
    vector = Column(Vector(768))

# Define Status Enum
class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

# Add these new classes to models.py

class CollabRequest(Base):
    __tablename__ = "collab_requests"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(String, ForeignKey("users.id"))
    receiver_id = Column(String, ForeignKey("users.id")) # Owner of the project
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    status = Column(String, default=RequestStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id")) # Chat room is linked to a project
    sender_id = Column(String, ForeignKey("users.id")) 
    content = Column(Text)
    is_ai = Column(Boolean, default=False) # True if the message is from the Bot
    created_at = Column(DateTime, default=datetime.utcnow)