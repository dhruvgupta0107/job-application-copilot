from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Postgres connection string, e.g.
    # postgresql://user:password@localhost:5432/job_copilot
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/job_copilot"

    # Gemini API key (from https://aistudio.google.com/apikey) - used ONLY
    # for embeddings now, not chat/generation.
    google_api_key: str = ""

    # Embedding model + dimension - both via Gemini's API. Different Gemini
    # embedding models return different vector sizes (768 vs 3072 depending
    # on the model/account), so these must match whatever your account's
    # embedding_model actually returns. Run list_models.py if unsure.
    embedding_model: str = "models/embedding-001"
    embedding_dim: int = 3072

    # Hugging Face token (from https://huggingface.co/settings/tokens) - used
    # ONLY for chat/generation (JD parsing, rewriting, outreach drafting).
    huggingfacehub_api_token: str = ""

    # Chat model called via HF's Inference API. Availability varies by
    # account - if this default doesn't work, swap it via CHAT_MODEL in
    # .env to any instruct model from huggingface.co/models that shows
    # "Inference Providers" support on its model page.
    chat_model: str = "meta-llama/Llama-3.1-8B-Instruct"

    # Comma-separated list of allowed frontend origins for CORS, e.g.
    # "https://job-copilot.vercel.app,http://localhost:5173"
    # Defaults to "*" (allow all) for local dev - tighten this before
    # deploying publicly.
    cors_origins: str = "*"

    # How many resume chunks to retrieve per query
    retrieval_top_k: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
