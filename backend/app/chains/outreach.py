from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import get_llm
from app.core.retry import with_hf_retry

llm = get_llm(temperature=0.5)

EMAIL_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You write concise, warm cold emails from a fresher software engineer to a "
     "recruiter or hiring manager. Keep it under 120 words. No generic flattery. "
     "Reference 1-2 specific rewritten bullet points as proof of fit."),
    ("human",
     "Company: {company}\nRole: {role}\n\n"
     "My relevant tailored highlights:\n{bullets}"),
])

LINKEDIN_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You write short, informal LinkedIn connection/outreach messages (under 60 words) "
     "from a fresher to someone at the target company. Casual, not salesy."),
    ("human",
     "Company: {company}\nRole: {role}\n\n"
     "My relevant tailored highlights:\n{bullets}"),
])

email_chain = EMAIL_PROMPT | llm | StrOutputParser()
linkedin_chain = LINKEDIN_PROMPT | llm | StrOutputParser()


@with_hf_retry
def _invoke_email(company: str, role: str, bullets_text: str) -> str:
    return email_chain.invoke({"company": company, "role": role, "bullets": bullets_text})


@with_hf_retry
def _invoke_linkedin(company: str, role: str, bullets_text: str) -> str:
    return linkedin_chain.invoke({"company": company, "role": role, "bullets": bullets_text})


def draft_outreach(company: str, role: str, bullets: list[str]) -> dict:
    """
    Chain 4: Generate both a cold email and a LinkedIn message, grounded in
    the verified bullets from Chain 3 (not the raw resume) so outreach stays
    consistent with what was actually claimed to this specific company.
    """
    bullets_text = "\n".join(f"- {b}" for b in bullets)
    return {
        "email": _invoke_email(company, role, bullets_text),
        "linkedin": _invoke_linkedin(company, role, bullets_text),
    }
