from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.chains.pipeline import run_pipeline
from app.core.embeddings import embed_documents
from app.core.parsing import chunk_text, extract_text
from app.database import get_db
from app.models import Application, ResumeChunk
from app.schemas import ApplicationResponse, JDSubmitRequest, ResumeChunkIngestRequest

router = APIRouter()


@router.post("/resume-chunks", status_code=201)
def ingest_resume_chunk(payload: ResumeChunkIngestRequest, db: Session = Depends(get_db)):
    """Add one chunk of your resume/project docs to the knowledge base manually."""
    [embedding] = embed_documents([payload.content])
    chunk = ResumeChunk(source=payload.source, content=payload.content, embedding=embedding)
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return {"id": str(chunk.id), "source": chunk.source}


@router.post("/resume-upload", status_code=201)
async def upload_resume(
    file: UploadFile = File(...),
    source: str = Form("resume"),
    db: Session = Depends(get_db),
):
    """
    Upload a resume/project doc directly (.pdf, .docx, or .txt).
    Extracts text, splits it into chunks, embeds each chunk, and stores
    them all - no manual chunking needed.
    """
    file_bytes = await file.read()

    try:
        raw_text = extract_text(file.filename, file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from this file")

    chunks = chunk_text(raw_text)
    if not chunks:
        raise HTTPException(status_code=400, detail="No usable text chunks found after splitting")

    embeddings = embed_documents(chunks)

    stored = []
    for content, embedding in zip(chunks, embeddings):
        chunk = ResumeChunk(source=source, content=content, embedding=embedding)
        db.add(chunk)
        stored.append(chunk)

    db.commit()

    return {
        "filename": file.filename,
        "chunks_stored": len(stored),
        "preview": [c.content[:80] for c in stored[:5]],
    }


@router.post("/applications", response_model=ApplicationResponse, status_code=201)
def submit_application(payload: JDSubmitRequest, db: Session = Depends(get_db)):
    """
    Submit a job description. Runs the full chain (parse -> retrieve -> rewrite
    -> draft outreach) and returns the application with its tailored output.
    """
    application = Application(company=payload.company, role=payload.role, jd_text=payload.jd_text)
    db.add(application)
    db.commit()
    db.refresh(application)

    run_pipeline(db, application)
    db.refresh(application)
    return application


@router.get("/applications/{application_id}", response_model=ApplicationResponse)
def get_application(application_id: str, db: Session = Depends(get_db)):
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.get("/applications", response_model=list[ApplicationResponse])
def list_applications(db: Session = Depends(get_db)):
    return db.query(Application).order_by(Application.created_at.desc()).all()
