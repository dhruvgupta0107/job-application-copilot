# Job Application Copilot — Frontend

React + Vite frontend for the backend at `../job-copilot`.

## Setup

```bash
npm install
cp .env.example .env
# .env: set VITE_API_URL to wherever your backend runs (default http://localhost:8000)
npm run dev
```

Opens at `http://localhost:5173` by default. Make sure the backend is running
first (`uvicorn app.main:app --reload` in the backend folder) - the frontend
does nothing without it.

## Pages

- **Process JD** - paste a company/role/JD, watch the 4 chains stamp through
  in real time, get rewritten bullets + draft outreach back
- **Applications** - every application you've processed, shown as a
  processing stub; click one for the full tailored output
- **Knowledge base** - upload your resume/project docs directly (`.pdf`,
  `.docx`, `.txt`) to feed the retrieval chain

## Notes on the chain-progress visual

The backend currently runs all 4 chains in a single request/response (no
streaming yet). The frontend advances the visual stage-by-stage on a timer
while the real request is in flight, then reconciles with the actual
success/error once the response lands. If you later add Server-Sent Events
or WebSocket progress updates to the backend, swap the timer logic in
`SubmitApplication.jsx` for real per-stage events - the `ChainProgress`
component itself doesn't need to change, it just takes a `statuses` object.

## Design

- Ink navy background, parchment card surfaces, gold/rust/moss accent colors
- Fraunces (display), Inter (body), JetBrains Mono (data/JD/JSON text)
- Signature element: each chain stage gets a real "stamp" as it completes,
  and each application in the list looks like a processing stub with a
  perforated edge - both extend the literal "application processing" theme
