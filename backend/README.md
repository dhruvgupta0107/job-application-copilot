# Job Application Copilot

Automates the tailoring work I was doing manually across 30+ job applications:
paste a JD → get resume bullets rewritten to match it → get a draft cold email
and LinkedIn message → everything logged in Postgres for tracking.

## Architecture

```
JD text  ->  Chain 1: JD Parser        (extract skills/seniority as JSON)
         ->  Chain 2: RAG Retrieval    (pgvector search over resume/project chunks)
         ->  Chain 3: Bullet Rewriter  (rewrite + guardrail chain rejects fabricated claims)
         ->  Chain 4: Outreach Drafter (cold email + LinkedIn message)
         ->  Postgres                 (applications + tailored_outputs tables)
```

Resume chunks and application data live in the same Postgres database
(via the `pgvector` extension), so there's one system of record instead of
a separate vector DB plus a separate relational DB.

**Models:** embeddings go through Gemini's API (`GOOGLE_API_KEY`). Chat/
generation (JD parsing, rewriting, outreach) goes through Hugging Face's
Inference API (`HUGGINGFACEHUB_API_TOKEN`). These are two separate API
keys/services - see Setup below.

## Setup

1. **Postgres with pgvector**
   ```sql
   CREATE DATABASE job_copilot;
   \c job_copilot
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **Environment**
   ```bash
   cp .env.example .env
   ```
   Fill in:
   - `DATABASE_URL` - your Postgres connection string (see Neon notes below
     if using Neon)
   - `GOOGLE_API_KEY` - from https://aistudio.google.com/apikey (used only
     for embeddings)
   - `HUGGINGFACEHUB_API_TOKEN` - from https://huggingface.co/settings/tokens
     (used only for chat/generation; a read-access token is enough)

   `EMBEDDING_MODEL`/`EMBEDDING_DIM`/`CHAT_MODEL` have defaults in
   `app/core/config.py` - only set them in `.env` if you need to override.

3. **Install deps**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Run**
   ```bash
   uvicorn app.main:app --reload
   ```
   Tables are created automatically on startup.

## Usage

1. **Upload your resume directly** (`.pdf`, `.docx`, or `.txt` - text is
   extracted and auto-chunked, no manual work needed):
   ```bash
   curl -X POST http://localhost:8000/resume-upload \
     -F "file=@/path/to/your_resume.pdf" \
     -F "source=resume"
   ```
   Repeat for other docs too (project READMEs, internship report, etc.) -
   just change `source` to something like `rag_chatbot_readme`.

   Alternatively, add a single chunk manually if you want more control over
   how something is split:
   ```bash
   curl -X POST http://localhost:8000/resume-chunks \
     -H "Content-Type: application/json" \
     -d '{"source": "resume", "content": "Built and deployed a RAG chatbot using FastAPI, LangChain, ChromaDB, and Gemini 2.0, deployed on Render/Vercel."}'
   ```

2. **Submit a job description**:
   ```bash
   curl -X POST http://localhost:8000/applications \
     -H "Content-Type: application/json" \
     -d '{"company": "Acme Corp", "role": "SDE-1", "jd_text": "<paste JD here>"}'
   ```
   Returns the application with `tailored_output`: rewritten bullets + draft
   email + draft LinkedIn message.

3. **List / fetch applications**:
   ```bash
   curl http://localhost:8000/applications
   curl http://localhost:8000/applications/{id}
   ```

## Why this design

- **Structured JD parsing before retrieval** - searching resume chunks by
  extracted skills instead of raw JD text avoids diluting the embedding with
  boilerplate (benefits, company blurb, etc.).
- **Guardrail chain on rewrites** - a second LLM call fact-checks all
  rewritten bullets in one batched call and drops anything that introduces
  a skill/tool that wasn't actually there. This is the main RAG failure
  mode (hallucinated claims) and it's handled explicitly rather than hoped
  away.
- **pgvector instead of a separate vector store** - keeps the whole system
  (tracking + retrieval) in one Postgres database, which is simpler to
  reason about and demo.
- **Split providers** - embeddings via Gemini, chat/generation via Hugging
  Face - keeps each provider to one job, so a quota problem on one side
  (e.g. chat rate limits) doesn't take down the other (retrieval keeps
  working even if generation is temporarily rate-limited).

## If the chat model gives a 404 or a rate-limit/quota error

Different Hugging Face accounts have access to different models via the
Inference API, and availability changes over time. If `CHAT_MODEL`'s
default doesn't work for your account:

1. Go to https://huggingface.co/models, filter by task (e.g.
   "Text Generation"), and find a model that shows Inference Providers
   support on its model page.
2. Set `CHAT_MODEL=<model_id>` in your `.env` (e.g.
   `CHAT_MODEL=mistralai/Mistral-7B-Instruct-v0.3`).
3. Check https://huggingface.co/settings/billing for your account's
   current usage/limits if you keep hitting rate limits.

The retry logic in `app/core/retry.py` only smooths over brief per-minute
rate limiting (waits 5s/15s/45s and retries up to 3 times) - it won't help
if your account's quota is fully exhausted for a billing period.

## Neon-specific notes

Neon's serverless Postgres can drop idle/long-running connections more
aggressively than a normal server, which can surface as
`SSL connection has been closed unexpectedly` mid-query. Two things help:

1. **Use Neon's pooled connection string.** In the Neon dashboard, the
   **Connect** modal has a toggle for "Connection pooling" - the pooled
   host usually looks like `ep-xxxx-pooler.us-east-2.aws.neon.tech`
   (note the `-pooler` suffix) instead of the direct host. Use that one in
   `DATABASE_URL`.
2. The engine already retries dead connections automatically
   (`pool_pre_ping=True` in `app/database.py`), so a single dropped
   connection shouldn't fail your request outright.

## If embeddings fail with a 404 "model not found" error

Gemini's available model names can vary by API key/project. Run
`list_models.py` (see above) to see exactly which embedding models your key
can use, then set `EMBEDDING_MODEL` in `.env` to one of them.

## If embeddings fail with a dimension mismatch error

If you change `EMBEDDING_MODEL` to something other than the default
`models/embedding-001` (3072-dim), update `EMBEDDING_DIM` in your `.env` to
match whatever that model actually returns (check the error message, or run
`list_models.py`), then reset your tables since the schema is fixed at
table-creation time:
```sql
DROP TABLE IF EXISTS tailored_outputs CASCADE;
DROP TABLE IF EXISTS resume_chunks CASCADE;
DROP TABLE IF EXISTS applications CASCADE;
```
Restart the backend afterward - tables get recreated automatically with the
new dimension.

## Note on the Postgres driver

This uses `psycopg` (v3), not `psycopg2`, because `psycopg2-binary` doesn't
yet ship prebuilt wheels for newer Python versions (e.g. 3.14) and fails to
build from source without Postgres dev headers (`pg_config`) installed.
`psycopg[binary]` avoids that entirely. Note the connection string uses
`postgresql+psycopg://` (not plain `postgresql://`) to tell SQLAlchemy to use
this driver.

## Deploying

**Backend → Render** (free tier works):
1. Push this `job-copilot` folder to a GitHub repo (or a subfolder of one)
2. In Render: New → Web Service → connect the repo. If using `render.yaml`
   (included), Render will pick up the build/start commands automatically -
   otherwise set manually:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Add environment variables in Render's dashboard: `DATABASE_URL`,
   `GOOGLE_API_KEY`, `HUGGINGFACEHUB_API_TOKEN`, and `CORS_ORIGINS` (set
   this to your deployed frontend's URL once you have it, e.g.
   `https://job-copilot.vercel.app` - comma-separate multiple origins)
4. Deploy. Render gives you a URL like `https://job-copilot-backend.onrender.com`

**Database → Neon** (already covered above) - use the **pooled** connection
string for a deployed backend, same as local.

**Frontend → Vercel:**
1. Push `job-copilot-frontend` to GitHub (can be the same repo, different
   subfolder, or a separate repo)
2. In Vercel: New Project → import the repo → set root directory to
   `job-copilot-frontend` if it's a subfolder
3. Add environment variable `VITE_API_URL` = your Render backend URL from
   above
4. Deploy. Vercel auto-detects Vite and handles build/output settings

**After both are deployed:** go back to Render and update `CORS_ORIGINS` to
your actual Vercel URL (it won't be known until after the frontend deploy),
then redeploy the backend so CORS allows it.

Note: Render's free tier spins down after inactivity - the first request
after idling can take 30-60s to wake up. Fine for a personal project, worth
knowing before a live demo.

## Next steps (not yet built)

- Company research chain (optional web search enrichment before outreach drafting)
- Auth (currently single-user, no login)
- Status transitions (drafted -> sent -> interview -> offer/rejected) with a UI
- Real per-stage streaming progress (SSE/WebSocket) instead of the frontend's
  timer-based visual approximation - see the frontend README for details

A React frontend already exists in the sibling `job-copilot-frontend`
project - point it at this backend via `VITE_API_URL`.
