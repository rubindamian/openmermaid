# Open Mermaid

Internal Nirvana studio for owned Mermaid diagrams. The **Django API** and **SvelteKit frontend** are independent deployable images. Compose can start all three locally; you can also run the API or the UI alone.

Sign-in is Google Workspace. Save publishes a public PNG. Google Docs keeps a snapshot at insert time — re-insert the image after a later Save to refresh a Doc. Browsers and Slack refetch.

## Setup

```bash
uv sync --group dev
source .venv/bin/activate
cp .env.example .env
cp frontend/.env.example frontend/.env
cd frontend && npm install && cd ..
```

Use Node 22+ (`nvm use` in `frontend/`). Fill `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env` before trying a real Google login.

### Corp TLS and image builds

Cloudflare WARP re-signs outbound TLS, so `uv` and `npm` inside a build reject PyPI and npm certificates (`invalid peer certificate: UnknownIssuer`, `SELF_SIGNED_CERT_IN_CHAIN`). Compose passes the host bundle at `/etc/corp-ca/ca-bundle.pem` as the `ca_bundle` build secret — share `/etc/corp-ca` in Docker Desktop's file sharing settings. Point `CORP_CA_BUNDLE` at a different path if yours differs. Off the corporate network the secret is optional and builds work without it.

## Run everything

```bash
docker compose up
```

- Studio UI: http://127.0.0.1:3000
- API: http://127.0.0.1:8082
- Health: http://127.0.0.1:8082/health/
- Postgres on the host: `localhost:5433`

## API only (no frontend process)

```bash
docker compose up backend postgres
```

The backend image does not start or contain the SvelteKit app.

Host-side Django against that database — `localhost:5433` is the default, so no overrides are needed:

```bash
uv run python manage.py migrate
uv run python manage.py runserver 0.0.0.0:8082
```

## Frontend only (against a remote or already-running API)

```bash
cd frontend
nvm use
cp .env.example .env   # set PUBLIC_API_ORIGIN
npm install
npm run dev
```

Or `docker compose up frontend` with `PUBLIC_API_ORIGIN` pointing at an API the **browser** can reach. The frontend container does not depend on the backend container.

## Tests

```bash
uv run pytest
cd frontend && npm test
```

## Quality

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## Environment

See `.env.example` for `POSTGRES_*`, `FRONTEND_ORIGIN`, `PUBLIC_API_ORIGIN`, and `GOOGLE_*`. Google login verifies the ID-token `hd` claim against `GOOGLE_WORKSPACE_DOMAINS`.
