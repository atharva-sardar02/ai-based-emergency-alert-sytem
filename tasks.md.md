# Alexandria EAS — MVP Pull Request Roadmap & Checklist (v0.1)

This plan assumes **Option A (FastAPI + SQLite → Postgres)** and reuses the current UI look from the prototype. Each PR lists concrete tasks and files to create/edit so you can track progress cleanly in GitHub.

---

## Repo Structure (after PR02)
```
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── routers/
│   │   │   └── alerts.py
│   │   ├── services/
│   │   │   ├── ingest_base.py
│   │   │   ├── ingest_nws.py
│   │   │   ├── ingest_usgs_eq.py
│   │   │   ├── ingest_nwis.py
│   │   │   ├── ingest_fires.py
│   │   │   └── classify.py
│   │   ├── utils/
│   │   │   ├── dedupe.py
│   │   │   └── time.py
│   │   └── settings.py
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   │   └── test_alerts.py
│   └── pyproject.toml (or requirements.txt)
├── frontend/
│   ├── public/
│   │   └── index.html  # derived from current prototype look
│   └── assets/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
└── Makefile (or scripts/)
```

---

## PR01 — Project Bootstrap & Tooling
**Goal:** Minimal runnable FastAPI server, tooling, and documentation skeleton.

**Tasks**
- [ ] Initialize repo, Python env (uv/venv/poetry) and pin core deps: `fastapi`, `uvicorn[standard]`, `pydantic`, `httpx`, `python-dotenv`.
- [ ] Create `backend/app/main.py` with `/api/health` endpoint.
- [ ] Add `.env.example` and config loader (`settings.py`).
- [ ] Write high-level `README.md` (run instructions, env variables).
- [ ] Add `.gitignore`, optional `pre-commit` config.

**Files (create/edit)**
- Create: `backend/app/main.py`, `backend/app/settings.py`, `.env.example`, `README.md`, `.gitignore`, `pyproject.toml` or `requirements.txt`, optional `Makefile`.

---

## PR02 — Database, Models & Alembic
**Goal:** SQLite by default, Alembic migrations, core tables.

**Tasks**
- [ ] Add SQLAlchemy + Alembic.
- [ ] Implement `database.py` (SessionLocal, engine, Base).
- [ ] Define models: `Alert`, `Classification`, `UserAction`.
- [ ] Migration: create tables and **unique index** on `Alert.natural_key`.

**Files**
- Create/Edit: `backend/app/database.py`, `backend/app/models.py`, `backend/app/schemas.py`, `alembic/env.py`, `alembic/versions/<timestamp>_init.py`.
- Update: `README.md` (DB setup & migrate).

---

## PR03 — Alerts API (List/Detail)
**Goal:** Serve alerts from DB with pagination and detail view.

**Tasks**
- [ ] Router `alerts.py`: `GET /api/alerts`, `GET /api/alerts/{id}`.
- [ ] Pydantic response schemas; include latest classification if present.
- [ ] Basic filtering: `?criticality=High|Medium|Low`, `?since=ISO8601`.
- [ ] Seed script to insert a few sample rows for local testing.

**Files**
- Create/Edit: `backend/app/routers/alerts.py`, `backend/app/schemas.py`.
- Create: `backend/app/tests/test_alerts.py` (smoke test).
- Update: `backend/app/main.py` (include_router), `README.md`.

---

## PR04 — Ingestion Framework + NWS Source
**Goal:** Pluggable ingestion framework and first source (NWS CAP alerts).

**Tasks**
- [ ] `ingest_base.py` interface: fetch → normalize → upsert.
- [ ] `ingest_nws.py`: pull recent alerts, map to schema, compute `natural_key`.
- [ ] `dedupe.py`: `natural_key(source, provider_id or title, area, rounded_time)`.
- [ ] Add simple scheduler (APScheduler) or CLI command for manual runs.

**Files**
- Create/Edit: `backend/app/services/ingest_base.py`, `backend/app/services/ingest_nws.py`, `backend/app/utils/dedupe.py`, `backend/app/utils/time.py`.
- Update: `backend/app/settings.py` (NWS endpoint), `README.md` (ingestion run).

---

## PR05 — Ingest USGS Earthquakes
**Goal:** Add second source for breadth and validate dedupe.

**Tasks**
- [ ] `ingest_usgs_eq.py`: fetch GeoJSON (M≥0), filter to region/time window.
- [ ] Normalize (magnitude → severity mapping), upsert with `natural_key`.

**Files**
- Create/Edit: `backend/app/services/ingest_usgs_eq.py`.
- Update: `README.md` (source config).

---

## PR06 — Ingest USGS NWIS (River Gauges)
**Goal:** Hydrologic signals; exercise differing payload shapes.

**Tasks**
- [ ] `ingest_nwis.py`: fetch latest levels/flows; produce alerts on threshold crossing.
- [ ] Normalize to schema (event_type: `Flood Watch/Warning` style or `Hydrology`).

**Files**
- Create/Edit: `backend/app/services/ingest_nwis.py`.
- Update: `README.md`.

---

## PR07 — Ingest Fires (NASA FIRMS/EONET)
**Goal:** Fire alerts for the area.

**Tasks**
- [ ] `ingest_fires.py`: fetch recent hotspots/events; bbox filter to Alexandria.
- [ ] Normalize; include source URL; upsert.

**Files**
- Create/Edit: `backend/app/services/ingest_fires.py`.
- Update: `README.md`.

---

## PR08 — Classification Worker (Local LLM + Rules Fallback)
**Goal:** Assign `criticality` High/Medium/Low using a small local model.

**Tasks**
- [ ] `classify.py`: poll for unclassified alerts, call local model (Ollama or llama.cpp).
- [ ] Persist to `Classification` with `model_version` & short `rationale`.
- [ ] Fallback rules when model offline (map severity/urgency → criticality).
- [ ] CLI entrypoint or scheduler job.

**Files**
- Create/Edit: `backend/app/services/classify.py`.
- Update: `backend/app/settings.py` (MODEL_NAME), `README.md` (model setup).

---

## PR09 — User Actions: Irrelevant & Acknowledge
**Goal:** API endpoints to mark irrelevant/acknowledged and filter list accordingly.

**Tasks**
- [ ] `POST /api/alerts/{id}/irrelevant` → insert `UserAction` record.
- [ ] `POST /api/alerts/{id}/acknowledge` (+ optional note).
- [ ] Default list hides `irrelevant` (add `?show_irrelevant=true` toggle).

**Files**
- Edit: `backend/app/routers/alerts.py` (new routes), `backend/app/schemas.py` (request/response), `backend/app/models.py` (enum if needed).
- Update: `README.md` (API examples).

---

## PR10 — Frontend Switch‑Over to API (Keep Same Look)
**Goal:** Use DB‑backed API instead of direct external calls.

**Tasks**
- [ ] Move current HTML into `frontend/public/index.html` and rewire JS fetch to `/api/alerts`.
- [ ] Wire buttons: Irrelevant → `POST /irrelevant`, Acknowledge → `POST /acknowledge`.
- [ ] Show badges for `criticality` and `acknowledged` state; provide toggle to view hidden.

**Files**
- Create/Edit: `frontend/public/index.html` (derived from current prototype), `frontend/assets/app.js` (fetch + UI handlers).
- Update: `backend/app/main.py` (serve static in dev or enable CORS), `README.md`.

> **Note:** Start from your uploaded `alexandria-dashboard-current.html` and port its markup/styles.

---

## PR11 — Docker & Config (Optional Postgres + Ollama)
**Goal:** One-command local run with DB and (optional) model server.

**Tasks**
- [ ] `docker-compose.yml` for Postgres + (optional) Ollama; networked to API.
- [ ] Update settings to accept `DATABASE_URL` for Postgres.
- [ ] Seed script and migration steps in `README.md`.

**Files**
- Create/Edit: `docker-compose.yml`, `backend/app/settings.py`, `README.md`.

---

## PR12 — Observability, Error Handling & Polish
**Goal:** Minimum operational hygiene.

**Tasks**
- [ ] Logging: ingestion successes/failures, classification results.
- [ ] Basic error responses and validation.
- [ ] Acceptance checklist pass; screenshots/gifs in README.

**Files**
- Edit: `backend/app/services/*.py`, `backend/app/routers/alerts.py`, `README.md`.

---

## Conventions & Tips
- **Branch naming:** `feat/ingest-nws`, `feat/classifier`, `chore/docker`, etc.
- **Commits:** small, imperative; reference PR number in follow-ups.
- **Testing:** Add at least a smoke test per API route and a dedupe test.
- **Env:** Begin with SQLite (`sqlite:///./alerts.db`), switchable via `DATABASE_URL`.
- **Time:** Store all timestamps in UTC; display in local time on UI.

---

## Acceptance Checklist (End of MVP)
- [ ] Ingestion creates unique rows (DB constraint) across all sources.
- [ ] `/api/alerts` paginates, filters by criticality, and includes latest classification.
- [ ] POST actions work and list hides irrelevant by default (toggle exists).
- [ ] Frontend loads from API and preserves the current visual style.
- [ ] Classification produces High/Med/Low with a short rationale, with rules fallback.
- [ ] Local run instructions verified from clean machine.

