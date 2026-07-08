import json

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import get_llm
from app.core.retry import with_hf_retry

llm = get_llm(temperature=0.3)

REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You rewrite resume bullet points to align with a target job description. "
     "Rules:\n"
     "1. You may ONLY use facts, tools, and experience present in the source bullets below.\n"
     "2. Do NOT introduce any skill, tool, or achievement that isn't already stated.\n"
     "3. You may rephrase, reorder, and emphasize - not invent.\n"
     "Respond ONLY with a JSON list of 3-4 rewritten bullet strings, no markdown fences."),
    ("human",
     "Target JD skills: {jd_skills}\n\n"
     "Source resume bullets (ground truth - do not go beyond this):\n{source_bullets}"),
])

# Guardrail checks ALL bullets in a single call instead of one call per bullet -
# cuts API calls significantly, which matters a lot on any free-tier quota.
GUARDRAIL_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a fact-checker. You'll be given source bullets (ground truth) and a "
     "JSON list of rewritten bullets to check. For EACH rewritten bullet, decide if "
     "every skill/tool/claim in it is supported by the source. "
     "Respond ONLY with a JSON list of booleans (true = pass, false = fabricated claim), "
     "in the same order as the input list, no markdown fences, no explanation."),
    ("human",
     "Source bullets:\n{source_bullets}\n\n"
     "Rewritten bullets to check (JSON list):\n{rewrites}"),
])

rewrite_chain = REWRITE_PROMPT | llm | StrOutputParser()
guardrail_chain = GUARDRAIL_PROMPT | llm | StrOutputParser()


def _parse_json_loose(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return json.loads(raw.strip().strip("```json").strip("```").strip())


@with_hf_retry
def _invoke_rewrite(jd_skills: str, source_bullets: str) -> str:
    return rewrite_chain.invoke({"jd_skills": jd_skills, "source_bullets": source_bullets})


@with_hf_retry
def _invoke_guardrail(source_bullets: str, rewrites: str) -> str:
    return guardrail_chain.invoke({"source_bullets": source_bullets, "rewrites": rewrites})


def rewrite_bullets(jd_skills: list[str], source_chunks: list[str]) -> list[str]:
    """
    Chain 3: Rewrite resume bullets to mirror JD language, then verify all
    rewrites against the source in a SINGLE guardrail call (not one call per
    bullet - keeps the pipeline to 2 LLM calls here instead of 5+, which
    matters on a rate-limited free tier). Bullets that fail are dropped.
    """
    source_bullets = "\n".join(f"- {c}" for c in source_chunks)

    raw = _invoke_rewrite(", ".join(jd_skills), source_bullets)
    candidates = _parse_json_loose(raw)

    if not candidates:
        return []

    verdict_raw = _invoke_guardrail(source_bullets, json.dumps(candidates))
    verdicts = _parse_json_loose(verdict_raw)

    # Defensive: if the model returns a mismatched-length list, fail open
    # (keep all bullets) rather than crash.
    if len(verdicts) != len(candidates):
        return candidates

    return [b for b, ok in zip(candidates, verdicts) if ok]
