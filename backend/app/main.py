from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import Base, engine
from app.routers import applications

app = FastAPI(title="Job Application Copilot", version="0.1.0")

# CORS_ORIGINS in .env can be "*" (dev) or a comma-separated list of exact
# origins (production), e.g. "https://job-copilot.vercel.app"
allowed_origins = (
    ["*"] if settings.cors_origins.strip() == "*"
    else [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(applications.router, tags=["applications"])


@app.on_event("startup")
def on_startup():
    # Creates tables if they don't exist. Requires the pgvector extension
    # to already be enabled on the database (see README).
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}
