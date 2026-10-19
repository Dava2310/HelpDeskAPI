# Project: "HelpDesk API" — a support ticket system

## Context
Learning project to practice FastAPI before building RAG/AI apps. You build it; Claude reviews each checkpoint to assert your knowledge. Difficulty: low-to-medium.

**Business problem:** A small company needs a backend for customer support. Customers open tickets and comment on them. Support agents pick up and resolve tickets. Admins manage users. Agents want live updates when tickets change.

## Functional Requirements
Each is testable; use the IDs in tests and commit messages.

**Auth & users**
- FR-1: A visitor can register with email + password (min 8 chars). Duplicate email -> 409. New users are `customer`.
- FR-2: A user can log in with email + password and receive a JWT access token (expires in 30 min). Bad credentials -> 401.
- FR-3: Any endpoint except `/health`, `/auth/register`, `/auth/login` requires a valid token; otherwise 401.
- FR-4: `GET /users/me` returns the current user (never the password hash).
- FR-5: Admin can list users (paginated) and change a user's role. Non-admins -> 403.

**Tickets**
- FR-6: A customer can create a ticket (title 5-100 chars, description, priority default `medium`). Status starts `open`; owner is the caller.
- FR-7: A customer lists/gets only their own tickets; another user's ticket returns 404.
- FR-8: Agents and admins list/get all tickets.
- FR-9: Ticket listing supports `limit` (default 20, max 100), `offset`, filter by `status` and `priority`, and sort by `created_at` (asc/desc).
- FR-10: A customer can edit title/description of their own ticket only while status is `open`.
- FR-11: An agent can assign an unassigned ticket to themselves; admin can assign to any agent. Assigning an already-assigned ticket -> 409.
- FR-12: Agents/admins change status following `open -> in_progress -> resolved -> closed`. A customer may reopen their own `resolved` ticket (-> `open`). Any other transition -> 409.
- FR-13: Only admins can delete a ticket (204); its comments are deleted too.

**Comments**
- FR-14: A ticket's owner, or any agent/admin, can add a comment to it. Closed tickets reject new comments (409).
- FR-15: Agents/admins can mark a comment `is_internal`; customers cannot (field ignored/422) and never see internal comments.
- FR-16: Comments are listed oldest-first, paginated.

**Real-time & streaming**
- FR-17: Agents/admins can open `WS /ws/tickets?token=...`; invalid token -> connection closed (code 1008).
- FR-18: On ticket create / status change / assignment, all connected agents receive a JSON event `{type, ticket_id, status, at}`.
- FR-19: Agents/admins can `GET /tickets/export` and receive all tickets as a streamed CSV (`StreamingResponse`).
- FR-20 (bonus): `GET /tickets/{id}/suggest-reply` streams a fake AI reply token-by-token via SSE.

**Non-functional**
- NFR-1: Config and secrets only via environment variables.
- NFR-2: Consistent error body `{"detail": ...}`; correct status codes (200/201/204/401/403/404/409/422).
- NFR-3: Schema changes only via Alembic migrations.
- NFR-4: Tests run against an isolated DB; `docker compose up` starts API + Postgres from scratch.
- NFR-5: Auto-generated OpenAPI docs are accurate (tags, summaries, response models).

## Roles & rules
- **customer**: register/login; create tickets; see and comment on ONLY their own tickets.
- **agent**: see all tickets; assign a ticket to themselves; change status; comment (including internal notes customers can't see).
- **admin**: everything an agent can do, plus list users and change their roles.
- Ticket status flow: `open -> in_progress -> resolved -> closed` (invalid transitions return 409).

## Data model
- `User`: id, email (unique), hashed_password, role, created_at
- `Ticket`: id, title, description, status, priority (low/medium/high), owner_id, assignee_id (nullable), created_at, updated_at
- `Comment`: id, ticket_id, author_id, body, is_internal, created_at

## Suggested stack
SQLModel (or SQLAlchemy 2.0) + SQLite first, then Postgres in Docker; Alembic for migrations; `pwdlib`/`argon2` for hashing; PyJWT; pytest + httpx.

## Phases (check in with Claude after each one)

### Phase 1 — Skeleton & design
1. Remove `src/`, use `app/` with: `main.py`, `config.py`, `database.py`, `models.py`, `schemas.py`, `routers/`, `dependencies.py`.
2. Settings via `pydantic-settings` and a `.env` file (no hardcoded secrets).
3. Design the endpoint list on paper BEFORE coding (resources, verbs, status codes, pagination).
4. Add `GET /health`.

**Checkpoint:** explain why separate request/response schemas, and what `APIRouter` and `Depends` give you.

### Phase 2 — Database & CRUD
1. Models + session dependency (`Depends(get_session)`).
2. Ticket CRUD (no auth yet): create, get, list with `limit/offset` + `status`/`priority` filters, patch, delete.
3. Comments as a nested route: `/tickets/{id}/comments`.
4. Correct status codes (201, 204, 404, 409), `response_model`, never return the password hash.
5. Add Alembic and generate the first migration.

**Checkpoint:** sync vs `async def` endpoints; what a session lifecycle is; why `response_model` matters.

### Phase 3 — Authentication
1. `POST /auth/register`, `POST /auth/login` (OAuth2 password form -> JWT with expiry).
2. `get_current_user` dependency using `OAuth2PasswordBearer`.
3. Hash passwords; never log them.

**Checkpoint:** what is inside a JWT, why hashing differs from encryption, how `Depends` chains work.

### Phase 4 — Authorization
1. `require_role(...)` dependency factory.
2. Ownership checks: customers get 404 (not 403) on tickets that aren't theirs.
3. Hide `is_internal` comments from customers.
4. Admin-only `/users` endpoints.

**Checkpoint:** 401 vs 403 vs 404; where authorization logic should live (dependency vs endpoint vs service function).

### Phase 5 — Testing
1. pytest + `TestClient`, a separate in-memory/test DB via `app.dependency_overrides`.
2. Fixtures: client, db session, users per role, auth headers.
3. Cover: auth happy/sad paths, each role's permissions, status transitions, pagination/filters.
4. Aim for ~80% coverage on routers (`pytest-cov`).

**Checkpoint:** why override dependencies instead of mocking; fixture scopes; what you chose NOT to test.

### Phase 6 — Docker
1. Multi-stage `Dockerfile` using uv (copy `pyproject.toml`/`uv.lock`, `uv sync --frozen`), run as non-root.
2. `docker-compose.yml`: `api` + `postgres` with healthcheck, volume, env file.
3. Run migrations on startup (or as a separate compose service).
4. `.dockerignore`.

**Checkpoint:** layer caching, why not bake secrets into the image, how the API reaches the DB inside the compose network.

### Phase 7 — Streaming / WebSockets (stretch)
1. `WS /ws/tickets` — authenticated (token as query param), agents receive live "ticket created/updated" events.
2. A simple in-memory `ConnectionManager` (broadcast to connected agents).
3. `GET /tickets/export` — CSV via `StreamingResponse` (generator, no full load in memory).
4. Bonus: SSE endpoint streaming a fake "AI suggested reply" token by token — direct preview of LLM streaming.

**Checkpoint:** limits of in-memory broadcast with multiple workers (and what Redis pub/sub would fix); WebSocket vs SSE.

## First steps (start here)
1. Create `app/` with `main.py` and `GET /health`; run `uv run fastapi dev app/main.py`.
2. Add `pydantic-settings` and `sqlmodel`; write the `User`, `Ticket`, `Comment` models.
3. Write the endpoint table (method, path, auth, roles, status codes) in `README.md`.
4. Show it to Claude — review the API design before writing routes.

## How each phase gets verified
- Run the app and exercise endpoints at `/docs`.
- `uv run pytest` passes; Claude reviews coverage and structure.
- `docker compose up` brings up a working API against Postgres.
- Connect with a WebSocket client (e.g. `websocat`) and see events when a ticket changes.
