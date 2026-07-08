from sqlalchemy.orm import Session

from app.chains.jd_parser import parse_jd
from app.chains.outreach import draft_outreach
from app.chains.retrieval import retrieve_relevant_chunks
from app.chains.rewriter import rewrite_bullets
from app.models import Application, TailoredOutput


def run_pipeline(db: Session, application: Application) -> TailoredOutput:
    """
    Runs the full chain: parse JD -> retrieve resume context -> rewrite bullets
    -> draft outreach -> persist everything back to Postgres.
    """
    # Chain 1
    parsed_jd = parse_jd(application.jd_text)
    application.parsed_jd = parsed_jd

    # Chain 2
    chunks = retrieve_relevant_chunks(db, parsed_jd)
    source_texts = [c.content for c in chunks]

    # Chain 3 (includes internal guardrail step)
    jd_skills = parsed_jd.get("required_skills", []) + parsed_jd.get("nice_to_have", [])
    verified_bullets = rewrite_bullets(jd_skills, source_texts)

    # Chain 4
    outreach = draft_outreach(application.company, application.role, verified_bullets)

    tailored = TailoredOutput(
        application_id=application.id,
        rewritten_bullets=verified_bullets,
        outreach_email=outreach["email"],
        outreach_linkedin=outreach["linkedin"],
        retrieved_chunk_ids=[str(c.id) for c in chunks],
    )
    db.add(tailored)
    db.commit()
    db.refresh(tailored)
    return tailored
