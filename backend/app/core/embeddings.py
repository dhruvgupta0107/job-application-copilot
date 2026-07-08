from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings
from app.core.retry import with_gemini_retry

embeddings = GoogleGenerativeAIEmbeddings(
    model=settings.embedding_model,
    google_api_key=settings.google_api_key,
)


@with_gemini_retry
def embed_text(text: str) -> list[float]:
    """Embed a single piece of text (used at query time)."""
    return embeddings.embed_query(text)


@with_gemini_retry
def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts (used at ingestion time)."""
    return embeddings.embed_documents(texts)
