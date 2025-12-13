import uuid
from datetime import datetime
import enum

from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    ARRAY
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from sqlalchemy import LargeBinary

from app.database import Base


#User Model OAuth Compatible
class User(Base):
    __tablename__ = "users"

    # Google email / sub ID
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    picture = Column(String)

    # Relationships
    projects = relationship(
        "Project",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    sent_requests = relationship(
        "CollabRequest",
        foreign_keys="CollabRequest.sender_id",
        back_populates="sender"
    )

    received_requests = relationship(
        "CollabRequest",
        foreign_keys="CollabRequest.receiver_id",
        back_populates="receiver"
    )

    messages = relationship(
        "ChatMessage",
        back_populates="sender"
    )

class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), unique=True)

    filename = Column(String)
    content_type = Column(String)
    data = Column(LargeBinary)

    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="file")

#Project Model with trending feature
class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.id"), index=True)

    title = Column(String, nullable=False)
    file_url = Column(String)
    abstract = Column(Text)
    topics = Column(ARRAY(String), default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    is_processed = Column(Boolean, default=False)

    # NEW: Trending support
    views_count = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="projects")
    embeddings = relationship(
        "Embedding",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    collab_requests = relationship(
        "CollabRequest",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    chat_messages = relationship(
        "ChatMessage",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    file = relationship(
        "ProjectFile",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan"
    )


#Embedding Model
class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))

    content = Column(Text)

    # Gemini embeddings (768 dims)
    vector = Column(Vector(768))

    project = relationship("Project", back_populates="embeddings")

#Collaboration Request
class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

class CollabRequest(Base):
    __tablename__ = "collab_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    sender_id = Column(String, ForeignKey("users.id"))
    receiver_id = Column(String, ForeignKey("users.id"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))

    status = Column(String, default=RequestStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sender = relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="sent_requests"
    )
    receiver = relationship(
        "User",
        foreign_keys=[receiver_id],
        back_populates="received_requests"
    )
    project = relationship("Project", back_populates="collab_requests")

#Chat Messages (Human + AI)
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    sender_id = Column(String, ForeignKey("users.id"))

    content = Column(Text)
    is_ai = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="chat_messages")
    sender = relationship("User", back_populates="messages")
