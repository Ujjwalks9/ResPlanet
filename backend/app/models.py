import uuid
from datetime import datetime
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