# AGENTS.md

Guidance for AI agents working in this repository. Follow the structure, conventions, and workflow below.
Also follow the general AI coding behavior guidelines in [GUIDELINES.md](GUIDELINES.md).

---

# Open Mermaid Development Guidelines

You are an expert in Python, Django, and split-origin web apps. Open Mermaid is an internal Mermaid studio: org Google login, owned diagrams in Postgres, and a public picture URL. The backend and frontend are **independent deployable images** so each can become its own EKS pod later.

## Core Principles

- **Django-First Approach**: Use Django's built-in features for the API, sessions, and ORM
- **Independent images**: Never merge the SvelteKit app into the Django image. Neither process may require the other on localhost except via configured URLs (`FRONTEND_ORIGIN`, `PUBLIC_API_ORIGIN`)
- **Code Quality**: Follow PEP 8; run pre-commit before considering work done
- **Naming Conventions**: lowercase_with_underscores for Python
- **Modular Architecture**: Product logic lives in `studio/`; settings live in `config/`
- **Security First**: Session cookies are HttpOnly, SameSite=Lax, and Secure in non-local environments

## Project Structure

```
openmermaid/
├── AGENTS.md
├── CLAUDE.md
├── GUIDELINES.md
├── README.md
├── pyproject.toml
├── uv.lock
├── manage.py
├── pytest.ini
├── conftest.py
├── .pre-commit-config.yaml
├── .env.example
├── docker-compose.yml          # postgres + backend + frontend
├── compose/local/django/       # independently runnable backend image
├── compose/local/frontend/     # independently runnable SvelteKit image
├── config/
│   ├── settings/               # base, local, production, test
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── studio/                     # Django app
├── tests/
├── frontend/                   # SvelteKit (later unit)
└── docs/plans/
```

## Local runtime

- Compose network: `nirvana_local` (created by this compose file)
- Host ports: Postgres `5433`, Django `8082`, frontend `3000`
- `docker compose up` starts frontend, backend, and Postgres
- `docker compose up backend postgres` is enough for API work
- Backend image listens on its own port and talks to Postgres via `POSTGRES_*`. It does not start or bundle the frontend
- Frontend image listens on its own port and calls the API via `PUBLIC_API_ORIGIN`
- Both builds take an optional `ca_bundle` secret (host `/etc/corp-ca/ca-bundle.pem`, override with `CORP_CA_BUNDLE`). Corp TLS interception otherwise breaks `uv` against PyPI and `npm` against the npm registry
- The backend image installs runtime dependencies only (`uv sync --locked --no-default-groups`); lint and test tooling stays on the host

## Django guidelines

- Split settings like ehr-bridge: `config/settings/{base,local,production,test}.py`
- Keep views thin; put product rules in `studio/`
- Unauthenticated health lives at `GET /health/`
- Google org login lives in `studio/auth.py` (`social-auth-app-django`). Do not copy ehr-bridge JWT consumer auth
- Diagram JSON API is session-authenticated; public PNG is unauthenticated `GET /p/{token}.png`

## Testing

- Tests live in `tests/` at the repo root
- Run with `uv run pytest` (`--ds=config.settings.test`)
- Prefer unit tests with the Django test client; mock Google and mermaid-cli when those units exist
- Add or update tests for new public behavior in the same change

## Development workflow

- Activate `.venv` (`source .venv/bin/activate`) or prefix commands with `uv run`
- Lint with `pre-commit run --all-files` before considering work done
- Python 3.13; `uv sync --group dev`

## Key conventions

1. Frontend and backend remain separate processes and images
2. Public PNG and Google callback must work without the frontend process (later)
3. Host Postgres is `5433` so it does not collide with ehr-bridge on `5432`
4. Env allowlists (`GOOGLE_WORKSPACE_DOMAINS`, `FRONTEND_ORIGIN`) are configuration, not hardcoded product rules
