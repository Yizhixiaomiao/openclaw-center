# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenClaw Center is an enterprise management platform for managing Windows VMs running AI agents. It consists of a FastAPI backend, Vue 3 frontend, and a Python Windows Agent client. The platform handles machine inventory, prompt template distribution, skill management, deployment orchestration, and monitoring.

## Development Commands

### Backend (from `backend/`)
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API docs available at `http://localhost:8000/docs`. Requires MySQL running on localhost:3306 with database `openclaw_center`.

### Frontend (from `frontend/`)
```bash
npm install
npm run dev          # dev server on :5173
npm run build        # production build
```
Vite proxy forwards `/api` requests to `http://localhost:8000`.

### Agent (from `agent/`)
```bash
pip install -r requirements.txt
python -m agent                           # run agent
pip install pyinstaller && python build.py # package as Windows EXE → agent/dist/
```

### Docker
```bash
docker-compose up -d   # starts MySQL + backend; frontend runs separately via npm
```

## Architecture

### Three-component system

- **Backend** (`backend/`): FastAPI serving REST APIs under `/api/`. SQLAlchemy ORM with MySQL, Pydantic v2 schemas, JWT auth. Auto-creates tables and seeds admin user on startup (`Base.metadata.create_all`).
- **Frontend** (`frontend/`): Vue 3 SPA with Element Plus UI, Pinia state, Vue Router with auth guards. Axios client at `src/utils/request.js` adds Bearer token and unwraps `response.data`.
- **Agent** (`agent/`): Python client that registers with the backend, sends heartbeats, collects system metrics, syncs prompts/skills, and executes tasks. Config via `config.yaml`.

### Backend route organization

All API routes in `backend/app/api/` follow the pattern: router → Pydantic schema validation → SQLAlchemy model → DB session. Routers are registered in `main.py` with `/api/` prefixes.

Key models: `User`, `Machine`, `AgentInfo`, `PromptTemplate`, `Skill`, `DeployTask`, `CodingPlan`, `AgentLog` — see `backend/app/models/__init__.py` for the full list.

### Frontend conventions

- Views organized by domain in `src/views/` (login, dashboard, users, machines, scenarios, prompts, skills, deploy, plans, monitor)
- API calls in `src/api/` modules, one per domain
- Route guards check `getToken()` and `meta.roles` for RBAC
- Element Plus components auto-imported via `unplugin-auto-import` + `unplugin-vue-components` — no manual imports needed for Element Plus

### Configuration

- Backend: `backend/app/config.py` — pydantic-settings, reads from `.env` file (DATABASE_URL, JWT_SECRET_KEY, ENCRYPTION_KEY, CORS_ORIGINS, UPLOAD_DIR)
- Frontend: `frontend/vite.config.js` — proxy, auto-import resolvers
- Agent: `agent/config.yaml` — server URL, heartbeat interval, log paths

### User roles

`admin`, `support`, `ops`, `manager`, `user` — enforced via `meta.roles` on frontend routes and backend endpoint checks.

## Key Patterns

- Backend uses `get_db()` dependency injection for DB sessions (SQLAlchemy `SessionLocal`)
- Frontend Axios interceptor auto-redirects to `/login` on 401
- Tables auto-created on startup (no Alembic migrations in use despite dependency being listed)
- Admin seed runs on every startup via `auth.seed_admin()`
- Default admin credentials: `admin` / `admin123`
