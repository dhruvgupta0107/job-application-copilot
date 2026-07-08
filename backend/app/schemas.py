import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JDSubmitRequest(BaseModel):
    company: str
    role: str
    jd_text: str


class ParsedJD(BaseModel):
    required_skills: list[str] = []
    nice_to_have: list[str] = []
    seniority: Optional[str] = None
    summary: Optional[str] = None


class TailoredOutputResponse(BaseModel):
    rewritten_bullets: list[str] = []
    outreach_email: Optional[str] = None
    outreach_linkedin: Optional[str] = None

    class Config:
        from_attributes = True


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    company: str
    role: str
    status: str
    parsed_jd: Optional[dict] = None
    created_at: datetime
    tailored_output: Optional[TailoredOutputResponse] = None

    class Config:
        from_attributes = True


class ResumeChunkIngestRequest(BaseModel):
    source: str
    content: str
