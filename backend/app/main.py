from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import applications

app = FastAPI(title="Job Application Copilot", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before deploying
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
