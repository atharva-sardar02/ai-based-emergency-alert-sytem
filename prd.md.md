# Product Requirements Document (PRD)

**Product:** Alexandria Emergency Alert System (MVP)

**Owner:** Atharva Sardar

**Version:** v0.1 (Draft for review)

**Goal:** Build a minimal but reliable pipeline that ingests alerts from 4–5 public APIs, deduplicates and stores them in a database, classifies criticality using a local/open‑source LLM, and serves a simple dashboard UI (same look & feel as current prototype) where users can mark items irrelevant, acknowledge, and view details.

---

## 1) Users & User Stories

### 1.1 Primary Users
- **Duty Officer / Emergency Manager** (City EOC staff)
- **Field Responder / Supervisor** (Fire/EMS/Police supervisors)
- **Civic Ops Analyst** (Data/ops team triaging signals)
- **Resident Observer (future)** (Read‑only; not in MVP scope for auth)

### 1.2 User Stories (MVP)
- **As an Emergency Manager**, I want to see all new alerts from trusted sources consolidated in one list so that I can quickly assess what demands attention.
- **As an Emergency Manager**, I want to label an alert as *acknowledged* (and optionally add a short note) so that my team knows we’re on it.
- **As an Analyst**, I want the system to automatically classify criticality (High/Medium/Low) so that I can triage faster.
- **As an Analyst**, I want to mark an alert as *irrelevant* so that noise is suppressed for the team.
- **As a Supervisor**, I want to open an alert’s detail page to view its raw payload, provenance, and timestamps so that I can validate and escalate appropriately.

### 1.3 Non‑MVP / Later
- User accounts/roles with SSO.
- Push notifications / SMS.
- Map visualizations with polygons.
- Mobile app.

---

## 2) Scope (MVP)

### 2.1 In‑Scope
- **Data ingestion** from ~4–5 sources (e.g., NWS Alerts, USGS Earthquakes, USGS NWIS river gauges, NASA FIRMS/EONET fires, WMATA incidents).
- **Normalization** into a common alert schema (title, summary, event type, severity, urgency, area, timestamps, source, url, raw payload).
- **Deduplication & uniqueness** using a deterministic `natural_key` (e.g., `sha256(source + provider_id + effective_timestamp)`), with DB constraints to prevent duplicates.
- **Storage** in a relational DB (tables: `alerts`, `classifications`, `user_actions`).
- **Classification** via a local/open‑source LLM to assign **criticality** (High/Med/Low) using a lightweight prompt over normalized fields.
- **API** to serve paginated alerts, allow mark irrelevant/acknowledged, and fetch details.
- **Frontend**: keep existing look; load from API (DB‑backed) instead of calling external APIs directly.

### 2.2 Out‑of‑Scope (MVP)
- AuthN/AuthZ, multi‑tenancy, and audit logging (placeholder only).
- Realtime websockets; polling is acceptable.
- Advanced geospatial joins/polygons (store lat/lon if available, but no spatial queries required yet).
- Automated escalation workflows (email/SMS/Slack pagers).
- Full analytics and historical trend dashboards.

---

## 3) Functional Requirements

### 3.1 Ingestion
- The system shall run ingestion jobs on a schedule (e.g., every 1–5 minutes per source).
- Each source module shall:
  - Fetch the latest items (with a time window buffer to avoid gaps) and parse JSON/CSV as needed.
  - Normalize fields to the common schema.
  - Compute `natural_key` and attempt insert; duplicates must be ignored by DB constraint.
  - Persist raw payload (JSON string) for provenance.

### 3.2 Deduplication
- **DB‑level uniqueness**: unique index on `natural_key`.
- Optionally, **soft de‑dupe** by title+area+rounded timestamp (e.g., 10‑min buckets), to handle sources with missing IDs.

### 3.3 Classification
- For new alerts, a background worker invokes a local/open‑source LLM (quantized small model) with a compact prompt to output `{criticality: High|Medium|Low, rationale: string}`.
- Persist the result to `classifications` table linked by `alert_id` and `model_version`.

### 3.4 User Actions
- **Mark Irrelevant**: persists `user_action = irrelevant` and hides it by default from the main list (toggle to show hidden).
- **Acknowledge**: persists `user_action = acknowledged` (+ optional note & timestamp/user).
- Detail page displays raw payload, timestamps, and provenance URL.

### 3.5 API Endpoints (MVP)
- `GET /api/alerts?since=…&criticality=…&page=…` – list alerts (DB‑backed, sorted by time desc).
- `GET /api/alerts/{id}` – details (+ raw payload snippet).
- `POST /api/alerts/{id}/acknowledge` – mark acknowledged (+ note optional).
- `POST /api/alerts/{id}/irrelevant` – mark irrelevant.

### 3.6 Frontend
- Preserve current layout/theme and urgency badges.
- Replace direct fetchers with calls to `/api/alerts`.
- Keep “👍 / 👎” buttons; wire them to `irrelevant`/`acknowledge` endpoints (or separate controls if preferred).

---

## 4) Non‑Functional Requirements
- **Reliability:** Ingestion jobs retry on transient errors; failed items logged with backoff.
- **Performance:** MVP target <500ms for `GET /api/alerts?page=1` (DB warm cache, 50 items).
- **Privacy/Security:** No PII in MVP; secure env var handling (.env). CORS limited to dev origin.
- **Observability:** Minimal logs for ingestion success/failure and classification results.
- **Dev Experience:** All services run locally via `uvicorn`/`node` + a single `docker-compose up` for DB (and optional Redis).

---

## 5) Data Model (MVP)

**alerts**
- `id` (PK)
- `natural_key` (unique)
- `source` (enum/text)
- `provider_id` (text; original ID if provided)
- `title`, `summary`, `event_type`, `severity`, `urgency`, `area`
- `effective_at`, `expires_at` (timestamps)
- `url` (text)
- `raw_payload` (jsonb/text)
- `created_at` (timestamp default now)

**classifications**
- `id` (PK)
- `alert_id` (FK → alerts.id)
- `criticality` (text enum: High|Medium|Low)
- `rationale` (text)
- `model_version` (text)
- `created_at` (timestamp)

**user_actions**
- `id` (PK)
- `alert_id` (FK)
- `action` (enum: acknowledged|irrelevant)
- `note` (text nullable)
- `actor` (text nullable; placeholder for future auth)
- `created_at` (timestamp)

Indexes on `(effective_at)`, `(source, provider_id)`, `(criticality)`.

---

## 6) Tech Stack – Options & Recommendation

### Option A — **FastAPI + SQLite/Postgres + Background Tasks (Recommended for easiest MVP)**
- **Why:** Very fast to scaffold; great typing; simple background tasks; excellent async HTTP clients; Python ecosystem for CSV/JSON is strong; easy to run locally.
- **Components:**
  - API: **FastAPI** (Pydantic models, dependency injection, OpenAPI docs)
  - Ingestion: **APScheduler** or simple cron + asyncio (per‑source jobs)
  - DB: **SQLite** for day‑1 (file‑based) or **Postgres** (Docker) for multi‑user dev; **SQLAlchemy** ORM, alembic migrations
  - Cache/Queue (optional): **Redis** (for rate limits, job queues)
  - LLM: **llama.cpp / ollama** running a small instruct model (e.g., 3–7B quantized) for offline classification
  - Container: **Docker Compose** for DB (+ model server if using Ollama)

**Pros:** Quickest to implement; simple local story; rich parsing libs; strong typing.  
**Cons:** Python concurrency for high‑throughput may need tuning; model server adds a process.

### Option B — **Node.js (Express/Nest) + Postgres + Prisma**
- **Why:** JS/TS end‑to‑end; Prisma DX is excellent; easy to deploy.  
- **Components:** Express or **NestJS** (DI + modules), **Prisma** ORM, **node‑cron** for ingestion, **pg** for DB. LLM via **Ollama** process.

**Pros:** TS types across stack; Prisma migrations; large ecosystem.  
**Cons:** CSV/geo parsing less ergonomic than Python; worker separation recommended later.

### Option C — **Supabase (hosted Postgres) + Edge Functions (Deno) + Minimal API**
- **Why:** Offloads auth/storage later; super fast to get DB + REST; can still run locally with Supabase CLI.  
**Pros:** Batteries‑included DB + auth later; Row‑level security.  
**Cons:** Adds cloud dependency; LLM local integration less direct; rate limits.

**Recommendation for MVP:** **Option A (FastAPI)** with **SQLite → Postgres** path. It’s the fastest way to a working, testable pipeline and plays nicely with local LLM classification.

---

## 7) LLM Classification (MVP)
- Run a small local model (e.g., 3–7B instruct) via **Ollama** or **llama.cpp**; store `model_version` (e.g., `llama3.2-3b-instruct‑Q4_K_M`).
- Input features: `source`, `event_type`, `severity`, `urgency`, `summary`, `area`, `effective_at`.
- Output: `criticality` (High/Med/Low) + `rationale` (1–2 sentences max). Enforce JSON output with a schema‑guard.
- Fallback: If model unavailable, default rules‑based mapping from severity/urgency.

---

## 8) Key Features (MVP Breakdown)
1. **Unified Alerts List** (paginated, newest first).  
2. **One‑click Irrelevant** (hide from main feed by default).  
3. **Acknowledge + Note** (adds badge on card and timestamp).  
4. **Detail Drawer/Page** (raw payload, provenance link).  
5. **Criticality Labels** (from LLM; colors consistent with UI).  
6. **Provenance Panel** (active sources represented).  

---

## 9) Pitfalls, Risks & Mitigations
- **API Rate Limits / Outages:** Backoff + jitter; cache last page; widen time windows; idempotent inserts.
- **Clock Skew / Timezones:** Normalize to UTC; store provider `sent/onset` times separately; display local time in UI.
- **Deduping False Positives:** Prefer provider IDs when available; else hash (`title + area + rounded_time + source`).
- **LLM Drift / Hallucinations:** Keep prompt minimal; cap rationale length; log decisions; add rules fallback.
- **CORS & Mixed Origins:** All data flows through backend API; frontend only hits `/api/*`.
- **Large Payloads:** Store raw JSON compressed or truncated with separate `raw_payload_full` table if needed.
- **Classification Latency:** Run classification async; UI shows rule‑based urgency immediately; replace when LLM result arrives.

---

## 10) Milestones & Deliverables

**M1 — Skeleton (1–2 days)**  
- FastAPI project, `alerts` table + unique index, `/api/health`.  
- Ingestion for 1 source (NWS).  

**M2 — Multi‑Source Ingestion (2–3 days)**  
- Add USGS EQ, USGS NWIS, one fire source (FIRMS/EONET), WMATA (if key).  
- Normalization + dedupe.

**M3 — LLM Classification (1–2 days)**  
- Local model via Ollama; write classifier worker; persist results.  

**M4 — Frontend Switch‑over (1–2 days)**  
- Replace direct fetchers with `/api/alerts`; wire 👍 (irrelevant) and acknowledge actions.  

**M5 — Detail View & Notes (1 day)**  
- Detail page/drawer; store notes on acknowledge.

**M6 — Polish & Docs (1 day)**  
- Error states, logging, .env, README.

---

## 11) Acceptance Criteria
- Ingestion stores unique alerts for all configured sources with no duplicate rows over repeated runs.
- `/api/alerts` returns correct pagination and includes LLM criticality when available.
- UI shows newest alerts first, supports irrelevant + acknowledge, and opens a detail view.
- System runs locally (developer mode) with a single command set (README instructions).

---

## 12) Open Questions
- Do we need simple keyword filters per source (e.g., only Alexandria bbox) in MVP or post‑MVP?
- Keep 👍 meaning “relevant” or repurpose to explicit *Acknowledge* button?
- Should we store basic geo (lat/lon) now for future map views?

---

## 13) Appendix — Implementation Sketch (Option A)

**Processes**
- `api` (FastAPI): serves endpoints; triggers background tasks (manual).
- `ingestor` (script/cron): runs each N minutes; writes to DB.
- `classifier` (worker): polls for unclassified alerts; calls local LLM.
- `db` (Postgres via Docker; SQLite acceptable for day‑1).

**Directory**
```
backend/
  app/
    main.py            # FastAPI app
    models.py          # SQLAlchemy ORM
    schemas.py         # Pydantic
    routers/
      alerts.py        # list/detail/actions
    services/
      ingest_nws.py    # per-source
      ingest_usgs_eq.py
      ingest_nwis.py
      ingest_fires.py
      ingest_wmata.py
      classify.py      # LLM client
    utils/
      dedupe.py        # natural_key helpers
  alembic/
  .env.example
frontend/
  (reuse current UI; swap fetch to /api/alerts)
```

**.env example**
```
DATABASE_URL=sqlite:///./alerts.db   # or postgres://...
FIRMS_API_KEY=...
WMATA_API_KEY=...
MODEL_NAME=llama3.2:3b-instruct-q4
```

