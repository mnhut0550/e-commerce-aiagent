from sqlalchemy import (
    create_engine, Column, String, Integer, DateTime, ForeignKey, Index, Text
)
import enum
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import func
from sqlalchemy.orm import scoped_session
import uuid


Base = declarative_base()


# ==========================================
# MAIN MODELS
# ==========================================


class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    session_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="messages")
    
    __table_args__ = (
        Index("idx_messages_session_id", "session_id"),
        Index("idx_messages_session_created", "session_id", "created_at"),
        Index("idx_messages_role", "role"),
        Index("idx_messages_session_id_desc", "session_id", "id"),
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    action = Column(String(100))
    detail = Column(String(255))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


# Engine & Session - PRODUCTION SETTINGS
DATABASE_URL = "postgresql://agentuser:agentpassword@postgres:5432/agentdata"

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,               # Realistic for 1000+ users
    max_overflow=30,            # Total 50 connections max
    pool_pre_ping=True,         # Health check before use
    pool_recycle=1800,          # Recycle after 30 min
    pool_timeout=10,            # Fail fast instead of hanging
    echo=False,
    connect_args={
        "options": "-c statement_timeout=30000",
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
)

SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

# FastAPI dependency
def get_db():
    """
    FastAPI dependency injection for database sessions.
    Auto cleanup after request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        SessionLocal.remove()

