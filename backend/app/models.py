import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.config import settings
from app.database import Base

EMBEDDING_DIM = settings.embedding_dim


class ResumeChunk(Base):
    """
    A single chunk of your resume / project READMEs / internship report,
    stored with its embedding for retrieval.
    """
    __tablename__ = "resume_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String, nullable=False)          # e.g. "resume", "rag_chatbot_readme"
    content = Column(Text, nullable=False)            # raw chunk text
    embedding = Column(Vector(EMBEDDING_DIM), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Application(Base):
    """
    One row per job you're applying to. This is the system of record —
    the AI chains read from ResumeChunk and write their output back here.
    """
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    jd_text = Column(Text, nullable=False)
    parsed_jd = Column(JSON, nullable=True)           # output of Chain 1 (JD parser)
    status = Column(String, default="drafted")        # drafted -> sent -> interview -> rejected/offer
    created_at = Column(DateTime, default=datetime.utcnow)

    tailored_output = relationship(
        "TailoredOutput", back_populates="application", uselist=False,
        cascade="all, delete-orphan"
    )


class TailoredOutput(Base):
    """
    The generated artifacts for one application: rewritten bullets + outreach draft.
    Kept in its own table so applications stays lean and this can be regenerated
    without touching the application row.
    """
    __tablename__ = "tailored_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, unique=True)
    rewritten_bullets = Column(JSON, nullable=True)   # list[str], output of Chain 3
    outreach_email = Column(Text, nullable=True)      # output of Chain 4
    outreach_linkedin = Column(Text, nullable=True)   # output of Chain 4
    retrieved_chunk_ids = Column(JSON, nullable=True) # which ResumeChunk ids were used (for traceability)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="tailored_output")
