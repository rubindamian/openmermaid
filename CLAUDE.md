# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

See @AGENTS.md for full development guidelines, conventions, and patterns.

## Setup

```bash
uv sync --group dev
source .venv/bin/activate
uv run pre-commit install
```

Copy `.env.example` to `.env` before `uv run` (uv loads `.env` by default).

```bash
docker compose up -d
```

Image builds need the corp CA at `/etc/corp-ca/ca-bundle.pem` (shared in Docker Desktop) because Cloudflare WARP re-signs TLS; override the path with `CORP_CA_BUNDLE`.

Frontend-only against a running API:

```bash
cd frontend && npm install && npm run dev
```

Host-side Django against Compose Postgres (defaults to `localhost:5433`; keep `POSTGRES_HOST`/`POSTGRES_PORT` out of `.env` so Compose can override them for the container):

```bash
uv run python manage.py migrate
```

## Commands

```bash
# Lint, format (required before committing)
pre-commit run --all-files

# Tests
uv run pytest
uv run pytest tests/test_django_starts.py -v

# Dev server on the host (API on 8082; does not start the frontend)
uv run python manage.py runserver 0.0.0.0:8082

# Frontend on 3000
cd frontend && npm run dev
```

Health: `http://127.0.0.1:8082/health/`
Studio: `http://127.0.0.1:3000/`
Django admin: `http://127.0.0.1:8082/admin/`

## Architecture

**Open Mermaid** is a split-origin studio: a Django API and a SvelteKit frontend that ship as **separate container images**. Do not bake the frontend into the Django image. Compose starts `frontend`, `backend`, and `postgres` on network `nirvana_local`.

**Key modules:**
- `config/` — Django settings split (`base`, `local`, `production`, `test`), URLs, WSGI/ASGI
- `studio/` — auth, diagram API, mermaid-cli publish, public PNG
- `compose/local/django/` — independently runnable backend image (includes Chromium for mermaid-cli)
- `compose/local/frontend/` — independently runnable SvelteKit image
- `frontend/` — SvelteKit 2 studio UI: sidebar shell, dashboard with grid/list views, split editor. Styled with Tailwind 4 on native elements; no component library

**Request flow (target):** browser → frontend origin for UI, browser → API origin for session cookies and JSON. Public PNG and Google OAuth callback are served by the API without the frontend process.

## Project Config Notes

- Python 3.13; Django 6; dependencies managed by `uv` via `pyproject.toml`/`uv.lock` (`dependency-groups`: `test`, `dev`)
- Pre-commit: django-upgrade (target 6.0), black, isort, flake8, codespell, plus prettier / svelte-check for `frontend/`
- Tests in `tests/` at root; `pytest.ini` + `conftest.py`; `--ds=config.settings.test`
- Host ports: Postgres `5433`, Django `8082`, frontend `3000`. Avoids ehr-bridge on `5432`/`8081`.
