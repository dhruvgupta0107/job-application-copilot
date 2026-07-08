from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.embeddings import embed_text
from app.models import ResumeChunk


def retrieve_relevant_chunks(db: Session, parsed_jd: dict) -> list[ResumeChunk]:
    """
    Chain 2: Retrieve the most relevant resume/project chunks for this JD.

    Instead of embedding the raw JD text, we build the query from the
    structured skills extracted in Chain 1 - this gives cleaner retrieval
    than searching on a noisy full JD (boilerplate, benefits text, etc.
    would otherwise dilute the embedding).
    """
    skills = parsed_jd.get("required_skills", []) + parsed_jd.get("nice_to_have", [])
    query_text = ", ".join(skills) if skills else parsed_jd.get("summary", "")

    query_embedding = embed_text(query_text)

    # pgvector cosine distance search: <=> operator via the pgvector SQLAlchemy type
    stmt = (
        select(ResumeChunk)
        .order_by(ResumeChunk.embedding.cosine_distance(query_embedding))
        .limit(settings.retrieval_top_k)
    )
    return list(db.execute(stmt).scalars().all())
