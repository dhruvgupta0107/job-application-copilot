import json

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import get_llm
from app.core.retry import with_hf_retry

llm = get_llm(temperature=0)

JD_PARSER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You extract structured information from job descriptions. "
     "Respond ONLY with valid JSON, no markdown fences, no preamble. "
     "Schema: {{\"required_skills\": [...], \"nice_to_have\": [...], "
     "\"seniority\": \"...\", \"summary\": \"one sentence\"}}"),
    ("human", "Job description:\n\n{jd_text}"),
])

# LCEL chain: prompt -> LLM -> string
jd_parser_chain = JD_PARSER_PROMPT | llm | StrOutputParser()


@with_hf_retry
def _invoke_jd_parser(jd_text: str) -> str:
    return jd_parser_chain.invoke({"jd_text": jd_text})


def parse_jd(jd_text: str) -> dict:
    """
    Chain 1: Turn a raw job description into structured JSON
    (required_skills, nice_to_have, seniority, summary).
    This structured output is what drives the retrieval query in Chain 2 -
    we search resume chunks by extracted skills, not the raw JD text.
    """
    raw = _invoke_jd_parser(jd_text)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Model occasionally wraps output in fences despite instructions - strip and retry once
        cleaned = raw.strip().strip("```json").strip("```").strip()
        return json.loads(cleaned)
