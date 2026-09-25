# Strategic Portfolio Alignment Portal

A centralized web application for a Data Analytics org to manage business requests through a
four-stage funnel: **Demand → Portfolio → Roadmap → Project Execution**. Built as a job
assessment for a Databricks-focused application development role.

This is **not** a Jira replacement — it sits earlier in the lifecycle, helping the organization
capture, evaluate, prioritize, resource and schedule strategic requests before they become
execution tickets.

## Architecture

```
React (Vite)  ──REST/HTTPS──>  Flask API  ──>  PostgreSQL   (operational source of truth)
                                    │
                                    └──>  AnalyticsProvider  ──>  Local (Postgres aggregation, active)
                                                              └─>  Databricks (stub, see below)
```

- **Frontend**: React + Vite, React Router, TanStack Query for server state, Recharts for
  dashboard charts. Plain CSS with design tokens (no UI kit dependency).
- **Backend**: Flask, chosen over FastAPI/Django to match the team's stated Flask expectation.
  Flask-SQLAlchemy for the ORM, Flask-Migrate/Alembic for migrations, Flask-JWT-Extended for
  auth, Marshmallow for request validation.
- **Database**: PostgreSQL — the transactional source of truth for demands, projects, workflow
  state, and audit data.
- **Analytics layer**: see [Databricks / analytics abstraction](#databricks--analytics-abstraction) below.

## Repository structure

```
backend/
  app/
    models/       SQLAlchemy models (users, demands, projects, roadmap, audit, notifications)
    schemas/       Marshmallow request-validation schemas
    api/            Flask blueprints (one per resource) + shared error handling/response envelope
    services/        Business logic: workflow state machine, audit logging, notifications
      analytics/      AnalyticsProvider interface + local (Postgres) and Databricks (stub) implementations
    auth/            JWT identity + role-based access decorators
    seed.py           Demo data generator
  tests/              pytest: workflow transitions, RBAC enforcement, core API behavior
frontend/
  src/
    pages/            One page per required screen (Dashboard, Demand List, New Demand, ...)
    components/        Reusable UI: StatusChip, KpiCard, Layout, loading/empty/error states
    services/           API client modules, one per backend resource
    context/            Auth context (JWT + current user)
docker/
  docker-compose.yml   Local Postgres for development (optional — a native install works too)
```

## Setup

### 1. Database

Either run Postgres via Docker (`docker compose -f docker/docker-compose.yml up -d`) or point
at a native install. Then create the app + test databases:

```sql
CREATE USER portfolio_app WITH PASSWORD 'portfolio_app';
CREATE DATABASE portfolio_app OWNER portfolio_app;
CREATE DATABASE portfolio_app_test OWNER portfolio_app;
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
cp .env.example .env           # adjust DATABASE_URL if needed
pip install -r requirements.txt

flask --app wsgi db init       # first time only
flask --app wsgi db migrate -m "initial schema"
flask --app wsgi db upgrade
flask --app wsgi seed          # populates demo data

flask --app wsgi run --debug --port 5000
```

Run tests: `pytest` (uses `TEST_DATABASE_URL` / `portfolio_app_test`).

### 3. Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev                    # http://localhost:5173
```

### Demo accounts

Seeded by `flask --app wsgi seed`, all with password `Password123!`:

| Role | Email |
|---|---|
| Business Requestor | `requestor.finance@globaldata.example` (also one per business function) |
| Project Manager | `priya.nair@globaldata.example` |
| Management | `sarah.miller@globaldata.example` |
| Admin | `admin@globaldata.example` |

## Workflow state machines

**Demand**: `Draft → Submitted → Under Review → Clarification Required → Validated → Approved | Rejected`
The requestor can submit a Draft or respond to a Clarification Required demand; every other
transition (Under Review, Validated, Approved, Rejected) is a PM/Management/Admin review action.
All transitions are validated server-side in `app/services/workflow.py` — invalid transitions
return a `400` with the allowed next states.

**Project execution**: `Portfolio → Planned → In Progress → At Risk/Blocked → Completed`
A project only reaches `Planned` by being scheduled on the roadmap (`POST /api/roadmap`), which
itself requires at least one requirement and one assigned capability. This is enforced even
though the raw `PATCH /api/projects/{id}/status` endpoint's transition table would otherwise
allow `Portfolio → Planned` directly — the status endpoint explicitly rejects that target so the
roadmap's prerequisite checks can't be bypassed.

## Role-based access control

Roles: `requestor`, `project_manager`, `management`, `admin`. Enforced via the `@require_role(...)`
decorator on every mutating route (`app/auth/decorators.py`) plus ownership checks in the service
layer (a requestor only sees/edits their own demands; a PM only manages their assigned projects).
Authorization is never inferred from what the frontend chooses to render.

## Databricks / analytics abstraction

`app/services/analytics/` defines an `AnalyticsProvider` interface (`get_funnel_counts`,
`get_kpis`, `get_distribution_by`, `get_roadmap_view`, `get_upcoming_milestones`). The dashboard
API routes depend on this interface, not on a concrete implementation.

- `local_provider.py` — the active implementation, aggregating live PostgreSQL data. Every
  dashboard number is computed from persisted workflow state; nothing is hard-coded.
- `databricks_provider.py` — a stub with the same method signatures and a documented production
  shape: operational data in Postgres, periodically aggregated into Delta tables, queried via the
  Databricks SQL Connector against a SQL warehouse, governed through Unity Catalog. Swapping to
  it in production is a one-line config change (`ANALYTICS_PROVIDER=databricks`), not a rewrite
  of any route or frontend code. Not wired to a real workspace in this assessment — no Databricks
  credentials were available to build against.

## Authentication

Simplified local JWT auth against seeded users (no real enterprise SSO provider available for
this assessment). In production this would be swapped for the organization's SSO/OIDC provider;
because authorization already runs through `get_current_user()` + role checks rather than
anything session-specific, that swap only touches `app/api/auth.py` and `app/auth/decorators.py`.

## What's intentionally out of scope

Per the assessment's own "keep the scope focused" guidance, these were left out to prioritize a
complete, working core funnel over exhaustive feature coverage:

- Comments/collaboration UI (the `Comment` model and table exist; no API/UI wired up yet)
- Dependency-between-projects UI (model + relationship exist; no dedicated screen)
- A live Databricks workspace connection (see above — interface is real, connection is stubbed)
- Deployment/CI configuration (local-only; out of scope until requested)
