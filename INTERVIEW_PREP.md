# Portfolio App Deep Dive

*A folder-by-folder, decision-by-decision walkthrough of this codebase, written for interview prep. Also published as a live doc at https://claude.ai/code/artifact/82ec4071-625a-42c3-9212-b3cc9c0ef754 — that copy stays editable/commentable; this file is a static snapshot for offline reading and version control.*

## What this is

A centralized web app for a Data Analytics org's PMO to manage business requests through a four-stage funnel: **Demand → Portfolio → Roadmap → Project Execution**. It's the assessment for an application-development role on a Databricks-focused team.

**The one-sentence pitch:** "One controlled entry point for business requests, so a business unit can submit a problem, a PMO can validate and resource it, leadership can schedule and prioritize it, and a project manager can execute and track it — all from one source of truth instead of scattered spreadsheets and email threads."

**How each stage works, and who owns it:**

| Stage | What happens | Who does it |
|---|---|---|
| Demand | A business requestor submits a problem statement, priority, and expected outcome | Business Requestor |
| Portfolio | The demand is validated, enriched with requirements and required capabilities (Data Engineering, Power BI, App Dev, AI/ML), and assigned a PM | Project Manager / PMO |
| Roadmap | The now-portfolio-ready project is scheduled to a quarter with planned start/end dates | Project Manager |
| Execution | The project is tracked through status (Planned → In Progress → At Risk/Blocked → Completed), milestones, and health | Project Manager |

**Why this isn't "just another Jira":** Jira picks up *after* something is already a known, scoped execution ticket. This app sits *before* that — it's where a vague business problem gets turned into something worth putting in Jira in the first place. If asked "why not just use Jira for this," the answer is that Jira has no concept of an unvalidated business request, no approval gate, and no portfolio-level prioritization view — this app is the funnel that feeds Jira, not a replacement for it.

**Where it stands right now:** fully working end-to-end, demoable — a demand can go from submission through approval, conversion to a project, requirement/capability enrichment, roadmap scheduling, execution, and completion, with every step showing up live on the management dashboard and in the audit trail.

## Why this tech stack

Every choice here has an honest reason — useful, because interviewers probe exactly this ("why Flask over Django/FastAPI?").

**Flask, not FastAPI or Django.** The panel explicitly said the team's main technical expectation is "Python-based application development, particularly Flask." Purely on technical merit, FastAPI would arguably be a slightly better fit for this specific app — it has built-in Pydantic validation and native async, which suits a validation-heavy CRUD API with nested resources. But this is an assessment for a specific team with a stated stack preference, and matching that signal outweighs a marginal technical edge. The honest answer if pressed: "I'd have leaned FastAPI on pure technical merit for this shape of app, but you told me Flask is what the team works in, so I built it the way you'd actually maintain it, using Flask-Marshmallow for the validation FastAPI would've given me for free."

**React + Vite.** Fast dev server, no config overhead, and React's component model fits the many-small-reusable-pieces requirement (StatusChip, KpiCard, DataTable-style tables reused across 10 screens) directly.

**PostgreSQL, via SQLAlchemy + Flask-Migrate.** The assessment explicitly calls for Postgres as "the transactional source of truth" — relational integrity matters here (a project belongs to exactly one demand, a roadmap item belongs to exactly one project, foreign keys everywhere). SQLAlchemy's ORM plus Alembic-based migrations (via Flask-Migrate) gives versioned, reviewable schema changes instead of hand-written DDL.

**Neon for hosting Postgres (a pragmatic pivot).** Locally, both a native PostgreSQL install and Docker Desktop turned out to be broken/unavailable in the dev environment (missing binaries, and a blocked installer download). Rather than lose time fighting local infra, I moved to Neon — a free, serverless, always-on hosted Postgres that hands you a connection string in about a minute. The code has zero awareness of this: it's one environment variable (`DATABASE_URL`), because the app was already written against the SQLAlchemy abstraction rather than anything Postgres-specific.

**JWT auth against seeded users, not real SSO.** There's no enterprise identity provider available to integrate against in an assessment sandbox. Flask-JWT-Extended gives a realistic auth flow (login → signed token → role/identity resolved server-side on every request) without needing a fake OAuth server. Swapping this for real enterprise SSO/OIDC in production only touches two files (`api/auth.py` and `auth/decorators.py`), because authorization logic downstream depends only on "who is the current user and what's their role," not on how they got authenticated.

## Architecture at a glance

```
React (Vite)  ──REST/HTTPS──>  Flask API  ──>  PostgreSQL   (operational source of truth)
                                    │
                                    └──>  AnalyticsProvider  ──>  Local (Postgres aggregation, active today)
                                                              └─>  Databricks (interface defined, stubbed)
```

**The layering inside the backend, and why it exists:**

```
api/          <- Flask blueprints: parse request, call a service, shape the response. No business logic here.
services/     <- workflow rules, audit logging, notifications, analytics. This is where "can this happen" lives.
models/       <- SQLAlchemy models: the shape of the data, relationships, to_dict() serialization.
schemas/      <- Marshmallow: validates what comes IN over the wire before it ever reaches a service.
```

The reason this separation matters, and the direct answer to "how did you keep responsibilities clean": a route handler in `api/demands.py` never contains an `if` statement deciding whether a status transition is legal — it calls `assert_demand_transition()` in `services/workflow.py`. That means the *same* rule protects every caller of that function, including the seed script and any future route, and it's independently unit-testable without spinning up HTTP at all. If the rule changes, it changes in exactly one place.

**Request lifecycle, end to end:** a PATCH to change a demand's status hits a blueprint route → `require_role()` decorator resolves the JWT, loads the current user, checks role → Marshmallow schema validates the JSON body → the route loads the target row and calls into `services/workflow.py` to validate the transition → on success, `services/audit.py` writes an audit log row in the *same* database transaction → `services/notifications.py` optionally creates a notification → one `db.session.commit()` → a consistent `{success, data, error}` envelope goes back to the frontend.

## Repository structure, folder by folder

```
backend/
  app/
    models/        SQLAlchemy models — one file per domain cluster, not one per table
    schemas/       Marshmallow request-validation schemas
    api/           Flask blueprints, one per resource
    services/      business logic: workflow rules, audit, notifications, analytics
      analytics/   the AnalyticsProvider interface + implementations
    auth/          JWT identity resolution + the require_role RBAC decorator
    seed.py        realistic demo-data generator
  tests/           pytest: workflow transitions, RBAC, core API behavior
  migrations/      Alembic-generated schema migrations
frontend/
  src/
    pages/         one file per required screen
    components/     reusable UI: StatusChip, KpiCard, Layout, loading/empty/error states
    services/        one API-client module per backend resource, mirrors api/ 1:1
    context/          AuthContext: JWT + current user, app-wide
docker/              docker-compose.yml for local Postgres (documented alternative, unused — we're on Neon)
```

**Why `models/` is split by domain cluster, not by table:** `user.py` holds both `User` and `BusinessFunction` because they're always reasoned about together; `project.py` holds `Project`, `Requirement`, `Capability`, `ProjectCapability`, `RoadmapItem`, `Milestone`, and `Dependency` because they're all sub-records of a project's lifecycle and have circular-ish relationships to each other. One file per table would have meant constant cross-file jumping for anything touching a project.

**Why `services/` exists as a layer separate from `api/`:** so business rules are testable and reusable without an HTTP request. `services/workflow.py`'s transition functions are called directly in `tests/test_demand_workflow.py` without touching Flask's test client for the pure-logic cases, and the same audit-logging helper (`services/audit.py`) is called from every mutating route instead of being copy-pasted seven times.

**Why `services/analytics/` is its own subpackage:** it's the one place in the codebase explicitly designed around a future swap (Postgres-backed today, Databricks-backed later) — see the dedicated section below.

**On the frontend, `services/` mirrors `api/` deliberately.** `frontend/src/services/demands.js` has one function per `backend/app/api/demands.py` route. A reviewer (or you, six months from now) can find the frontend call for any backend endpoint by name alone, no searching.

## Database schema and design rationale

14 tables. Grouped by what they're for:

**Identity:** `users` (name, email, password_hash, role, business_function_id), `roles` (baked in as a Python enum, not a table — see below), `business_functions`.

**Demand stage:** `demands` (title, problem_statement, priority, status, requestor_id, business_function_id), `demand_reviews` (an append-only log of every review action: who, what action, comments, when — separate from `demands` itself so the history survives even as the demand's current fields change).

**Portfolio stage:** `projects` (1:1 with the `demand` that spawned it via a unique `demand_id`), `requirements` (many per project, free text + category), `capabilities` (a small lookup table: Data Engineering, Power BI, Application Development, AI/ML, Other), `project_capabilities` (the many-to-many join table between projects and capabilities, carrying an `effort_estimate` — this is *why* it's a real table and not just a list column: the relationship itself has data on it).

**Roadmap + execution:** `roadmap_items` (1:1 with project, via unique `project_id` — a project is either scheduled or it isn't; quarter, sequence, planned start/end), `milestones` (many per project), `dependencies` (self-referential: a project can depend on another project).

**Cross-cutting:** `comments` (polymorphic via `entity_type`/`entity_id`, so both demands and projects can be commented on through one table — model exists, no UI built yet), `audit_logs` (user, action, resource_type/resource_id, old_value, new_value, timestamp, request_id), `notifications` (per-user, typed, read/unread).

**A few deliberate choices worth being able to defend:**

- **Roles are a Python enum on the `users` table, not a separate `roles` table with a foreign key.** There are exactly four roles, they're not user-editable data, and a real `roles` table would be a join for no benefit at this scale. If the app needed dynamic, admin-configurable roles later, that's the natural point to promote it to a table.
- **`RoadmapItem` is its own table, not columns bolted onto `Project`.** A project's roadmap state (quarter, sequence, planned dates) is genuinely optional and stage-specific — most projects don't have one yet. Modeling it as a separate table means `project.roadmap_item is None` is a clean, direct way to ask "is this on the roadmap," instead of checking whether three nullable columns happen to all be set.
- **Every foreign-key-heavy list column that gets filtered on (`demands.status`, `projects.status`, `audit_logs.resource_type/resource_id`, etc.) has an explicit index** — the assessment's own quality checklist calls for "database indexes for common filters," and dashboard/list queries filter on exactly these columns.

## Workflow state machines

**Demand:** `Draft → Submitted → Under Review → Clarification Required → Validated → Approved | Rejected`

The requestor can only trigger two of these transitions themselves: submitting a Draft, or responding to a Clarification Required demand (which sends it back to Under Review). Every other transition — moving to Under Review, Validated, Approved, or Rejected — is a PM/Management/Admin-only review action via a separate `POST /demands/{id}/review` endpoint. That split is enforced in two places on purpose: the RBAC decorator (`@require_role(...)`) gates *who* can call the endpoint at all, and a transition table gates *which* status changes are legal regardless of role.

**Project execution:** `Portfolio → Planned → In Progress → At Risk/Blocked → Completed`

Both machines are implemented the same way — not as scattered `if` checks, but as explicit adjacency dictionaries in `services/workflow.py`:

```python
DEMAND_TRANSITIONS = {
    DemandStatus.DRAFT: {DemandStatus.SUBMITTED},
    DemandStatus.UNDER_REVIEW: {DemandStatus.CLARIFICATION_REQUIRED, DemandStatus.VALIDATED, DemandStatus.REJECTED},
    # ...
}
```

A route never mutates `.status` without first calling `assert_demand_transition(current, target)`, which raises a `WorkflowError` (→ a clean 400 with the allowed next states listed) if the target isn't in the current state's allowed set. This is what the assessment's own "invalid workflow transitions should return a clear API validation error" requirement is asking for, implemented literally.

**The one deliberately unusual rule:** a project can only reach `Planned` by being scheduled on the roadmap (`POST /api/roadmap`), which itself requires at least one requirement *and* one assigned capability first. It cannot reach `Planned` through the generic `PATCH /projects/{id}/status` endpoint — that endpoint explicitly rejects `Planned` as a target, with a message pointing at the roadmap endpoint instead. See "A bug I caught" below for why that rule exists and how it was found.

## RBAC and authentication

**Four roles:** `requestor`, `project_manager`, `management`, `admin`. Enforced in two layers, deliberately:

1. **Role gate** — `@require_role(*roles)` in `auth/decorators.py` wraps a route, resolves the JWT to a `User`, and 403s if their role isn't in the allowed set. Called with no arguments (`@require_role()`) it just means "any authenticated user."
2. **Ownership gate**, layered on top, inside the route or service — role alone isn't enough. A `requestor` can only see/edit *their own* demands (`Demand.requestor_id == user.id`), and a `project_manager` can only manage a project they're actually assigned to (`project.project_manager_id == user.id`), not any project a PM happens to exist for.

**Why server-side only, always:** the frontend's `NAV_ITEMS` and page guards (`ProtectedRoute` with a `roles` prop) hide UI a user shouldn't use, purely for UX — they are not a security boundary. Every mutating route re-checks role and ownership independently of what the frontend rendered, because a user can always call the API directly with curl/Postman regardless of what buttons they saw. This is the direct answer to "how do you prevent unauthorized actions": never trust the client, ever, for anything that matters.

**Auth flow:** `POST /api/auth/login` checks email + password hash (Werkzeug's `generate_password_hash`/`check_password_hash`, not rolled by hand) and returns a signed JWT via Flask-JWT-Extended. Every subsequent request carries that token in an `Authorization: Bearer` header; `get_current_user()` decodes it, loads the user fresh from the database (so a deactivated user is rejected immediately, not just at login time), and that's what every role/ownership check runs against.

**Simplified vs. real SSO:** this is JWT against seeded demo users, not a real enterprise identity provider — there wasn't one available to build against in an assessment sandbox. The design deliberately keeps the auth mechanism isolated from the authorization logic (nothing downstream cares *how* you proved who you are, only *who you are and what role you have*), so swapping to real SSO/OIDC later is a contained change to `api/auth.py`, not a rewrite of every protected route.

## The Databricks / analytics abstraction

This is the section most likely to get direct interview attention, since the role is explicitly Databricks-focused and there was no real Databricks workspace available to build against.

**The problem it solves:** the assessment brief asks for a "credible Databricks/data layer" demonstrating separation between operational data (Postgres) and analytical workloads (Databricks), without requiring a live connection. The answer is an interface, not a connection:

```python
# app/services/analytics/base.py
class AnalyticsProvider(ABC):
    def get_funnel_counts(self, filters: dict) -> dict: ...
    def get_kpis(self, filters: dict) -> dict: ...
    def get_distribution_by(self, field: str, filters: dict) -> list[dict]: ...
    def get_roadmap_view(self, filters: dict) -> list[dict]: ...
    def get_upcoming_milestones(self, limit: int = 10) -> list[dict]: ...
```

**`local_provider.py`** implements this today, querying Postgres directly for every dashboard number — funnel counts, KPI cards, distributions by business function/PM/priority, the roadmap timeline, upcoming milestones. Every value is computed live from persisted workflow state at request time; nothing on the dashboard is hard-coded, which is a specific item on the assessment's own quality checklist.

**`databricks_provider.py`** is a stub with the identical method signatures, carrying a documented production shape in its docstring rather than a fake implementation: operational data stays in Postgres as the transactional source of truth; a scheduled job or CDC pipeline periodically lands aggregated demand/project metrics into Delta tables; those are queried via the Databricks SQL Connector for Python against a SQL warehouse; access is governed through Unity Catalog, scoped to the same four roles the app already uses.

**The part worth saying explicitly in the interview:** the dashboard API routes (`api/dashboard.py`) depend on `get_analytics_provider()`, which reads one config value (`ANALYTICS_PROVIDER`) and returns whichever implementation is registered. Flipping that to `databricks` once a real workspace exists is a one-line config change — zero changes to any route, and zero changes to the frontend, because both only ever talk to the interface. That's the actual point of the pattern: it's not about faking Databricks, it's about proving the seam where it plugs in is already correctly placed.

## REST API design

**Blueprint per resource** — `auth`, `demands`, `projects`, `roadmap`, `dashboard`, `audit`, `notifications`, `lookups` — each registered under `/api/<resource>` in the app factory. 28 routes total, all discoverable by walking `app.url_map`.

**One consistent response envelope, everywhere:**

```json
{ "success": true, "data": { ... }, "error": null, "meta": { "page": 1, "total": 42 } }
```

`meta` only appears on paginated list endpoints. This is the assessment's "consistent API response/error structure" requirement, and it means the frontend never has to special-case how to unwrap a response — one `unwrap()` helper in `services/api.js` handles all of them.

**Validation happens before a route's logic ever runs.** Every mutating endpoint loads its body through a Marshmallow schema (`DemandCreateSchema`, `ProjectStatusUpdateSchema`, etc.) that enforces required fields, string lengths, and enum membership. A bad request never reaches the database layer.

**Error handling is centralized, not scattered.** `services/errors.py` defines a small hierarchy (`ApiError` → `WorkflowError`, `ForbiddenError`, `NotFoundError`), each carrying its own HTTP status code. `api/errors.py` registers Flask error handlers for these plus Marshmallow's `ValidationError` (→ 422) plus a catch-all `Exception` handler (→ 500, logged server-side, generic message to the client — no stack traces leak out). A route just `raise`s the right error type; it never constructs an error response by hand.

**Pagination** is real, not client-side slicing — `Query.paginate()` on every list endpoint, with `page`/`per_page`/`total`/`pages` in `meta`, matching the checklist's "pagination for lists" requirement directly.

## Frontend architecture

**TanStack Query, not Redux, for server state.** Almost everything the UI shows *is* server state — demands, projects, dashboard numbers, audit logs. TanStack Query gives caching, automatic refetch-on-invalidate after a mutation, and loading/error states for free, without hand-rolling a store and a set of reducers just to mirror what the API already owns. Redux (or any client-state library) would only earn its keep for state that's genuinely local and complex, which this app doesn't really have — the small bits of local UI state (form steps, filter selections) live in plain `useState`.

**`AuthContext`** holds the JWT and current user, persisted to `localStorage` so a refresh doesn't log you out, and exposes `login()`/`logout()`. `ProtectedRoute` reads it to gate whole routes by role; it's a UX convenience, not the security boundary (that's server-side, see the RBAC section).

**Service modules mirror backend blueprints 1:1** — `services/demands.js` has a function per `/api/demands/*` route, same for `projects.js`, `roadmap.js`, etc. `services/api.js` is the one shared axios instance: it attaches the JWT to every request via an interceptor, and on a 401 anywhere, clears the session and redirects to `/login` — centralizing "what happens when auth expires" in one place instead of every component handling it.

**Plain CSS with design tokens, not a UI kit.** `index.css` defines the whole visual system as CSS custom properties (`--color-primary`, `--space-4`, `--radius-md`, etc.) plus a small set of reusable component classes (`.card`, `.chip`, `.kpi-card`, `.data-table`). No Tailwind/MUI dependency to pull in for an app this size; every token is one place to change if the palette needs to shift.

**The 10 required screens map directly to `pages/*.jsx`:** Dashboard, DemandList, NewDemand (a 3-step guided form), DemandDetail (review actions + history), PortfolioWorkspace, Roadmap (quarter-column board), ProjectExecution, ProjectDetail (the shared full record for both Portfolio and Execution views), AuditHistory, AdminUsers. Reusable pieces (`StatusChip`, `KpiCard`, `Layout`, loading/empty/error state components) are shared across all of them rather than redefined per page.

## Testing strategy

13 pytest tests, covering the parts of the system where a silent bug would actually hurt: **workflow transitions** (`test_demand_workflow.py`) and **RBAC enforcement** (`test_rbac.py`).

Workflow tests assert both directions — not just that a legal transition succeeds, but that an illegal one is rejected with a 400 and a clear message. The RBAC tests assert the negative cases explicitly: a requestor gets 403 trying to review or convert a demand, gets 403 viewing someone else's demand, and only ever sees their own demands in a list response. Negative-path tests like these are the ones that actually catch authorization bugs; positive-path-only test suites tend to miss them.

**Why tests run against local SQLite instead of the real Neon Postgres:** the test fixtures call `db.create_all()`/`db.drop_all()` fresh for *every single test*, to guarantee test isolation — no test can see another test's data. Doing that over the network against a hosted database on every run would be slow and adds a network dependency to running the suite at all. SQLite in a temp file gives the same isolation guarantee in milliseconds. The trade-off is explicit and intentional: fast, isolated unit/integration tests locally, with the schema itself validated against real Postgres separately (the Alembic migration was generated and it also applies cleanly to Neon, which is not guaranteed automatically — SQLite and Postgres diverge on some type handling).

**What's verified by hand instead of by an automated test:** the full "Minimum Acceptance Demo" from the assessment brief — create demand → submit → review chain → approve → convert to project → add requirements/capabilities → assign PM → schedule on roadmap → start execution → add milestone → mark At Risk → confirm the dashboard KPIs updated live → confirm the audit trail recorded every step with old/new values. Walked end-to-end via curl against the running backend, which is a legitimate way to prove an integration path works even without a dedicated Playwright/E2E suite in the time available.

## A bug I caught — good material for "tell me about a bug you found"

While writing the test that checks a project can't jump straight to `In Progress` without a roadmap, I noticed a bigger hole underneath it: the generic `PATCH /projects/{id}/status` endpoint would let a project move from `Portfolio` straight to `Planned` directly — completely bypassing the rule that scheduling on the roadmap requires at least one requirement and one assigned capability first.

**Why it slipped through:** the transition *table* (`PROJECT_TRANSITIONS`) correctly listed `Portfolio → Planned` as valid, because that transition *is* legal — just only through the roadmap-scheduling endpoint, which does the prerequisite checks before setting the status. The generic status-update endpoint reused the same transition table for validity, but had no idea that this particular transition carried an extra precondition that lived somewhere else entirely.

**The fix:** explicitly reject `Planned` as a target in the generic status endpoint, with a message pointing at the roadmap endpoint instead — so the *only* code path that can ever set a project to `Planned` is the one that also enforces the requirements/capabilities check in the same transaction.

**Why this is worth bringing up unprompted:** it's a real example of a validation rule that looked complete (a transition table, tested, enforced) but had a gap because two different code paths could reach the same state through different rules. It's also a genuine "caught it myself before it shipped" story, not a hypothetical — the test I was writing to check something else is what surfaced it.

## Scope boundaries — what's deliberately out, and why

The source brief itself says to prioritize "a working business application over a large number of optional features." These are informed trade-offs made to protect that, not things that were missed:

- **Comments/collaboration UI.** The `Comment` model and table exist (polymorphic, ready for both demands and projects), but no API routes or screen were built on top of it. Reasoning: it's explicitly listed as a "nice to have" collaboration feature in the source material, not part of the core funnel or the Minimum Acceptance Demo checklist.
- **Dependencies-between-projects UI.** Same story — the `Dependency` model and relationship exist at the data layer, no dedicated screen. Useful for a roadmap view, not required for the core workflow to function end-to-end.
- **A live Databricks connection.** The interface (`AnalyticsProvider`) and the documented production shape are real; the connection to an actual workspace is not, because no Databricks credentials were available in this assessment context. Covered in detail above.
- **Real enterprise SSO.** JWT against seeded users instead — covered in the RBAC section.
- **Deployment/CI configuration.** Out of scope until asked for; the focus was a correct, demoable, locally-runnable application first.

**If asked "what would you build next with more time,"** the honest, ordered answer: (1) wire the existing `Comment` model up to a real endpoint + UI, since the data model is already there, (2) add Playwright E2E coverage for the full funnel instead of relying on manual curl verification, (3) connect `databricks_provider.py` to a real workspace once credentials exist, (4) add optimistic-locking or a `version` column for concurrent-edit protection on projects, since right now two PMs editing the same project simultaneously would silently last-write-wins.

## Anticipated interview Q&A

**"Why Flask over Django or FastAPI?"** → You told me Flask is the team's main expectation. On pure technical merit for a validation-heavy CRUD API, FastAPI's built-in Pydantic validation is a marginal edge, but matching your actual stack mattered more than a small technical preference — and Marshmallow gets me the same validation guarantees in Flask.

**"How would you prevent unauthorized status transitions?"** → Two layers: a role decorator gates who can call the endpoint, and an explicit transition-adjacency table gates which state changes are legal regardless of role — both enforced server-side, never trusted from the frontend.

**"How would you connect this to Databricks?"** → The `AnalyticsProvider` interface already exists; a real implementation would query a Databricks SQL warehouse via the Databricks SQL Connector, governed through Unity Catalog, and swapping it in is one config value — zero route or frontend changes.

**"How do you handle concurrent updates?"** → Honestly: not yet beyond database-level transaction isolation. The next thing I'd add is a `version` column with optimistic locking on `projects`, so two PMs editing the same project simultaneously get a conflict instead of silent last-write-wins.

**"Why Postgres?"** → Relational integrity matters here — a project belongs to exactly one demand, a roadmap item to exactly one project — and the brief explicitly asks for Postgres as the transactional source of truth, with Databricks handling analytical workloads separately.

**"How does this differ from Jira?"** → Jira starts once something is already a scoped, approved execution ticket. This app is everything *before* that: capturing an unvalidated business problem, deciding if it's worth doing, resourcing it, and scheduling it — the funnel that decides what's even worth creating a Jira ticket for.

**"How would you scale this?"** → The read-heavy dashboard queries are the first bottleneck — they're already isolated behind `AnalyticsProvider`, so caching or precomputed aggregates (or moving them to Databricks entirely) slots in without touching anything else. On the write side, indexes already exist on every commonly-filtered column (`status`, `business_function_id`, `project_manager_id`, etc.).

**"Tell me about a bug you caught."** → The `Planned`-status bypass — see "A bug I caught" above, it's a genuine, specific story, not a hypothetical.

**"What would you do differently with more time?"** → See "Scope boundaries" above — Comment UI, E2E tests, a real Databricks connection, optimistic locking, in that order.
