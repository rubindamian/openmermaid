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

### Corp TLS

Cloudflare WARP re-signs outbound TLS, so `uv` and `npm` inside a build reject PyPI and npm certificates (`invalid peer certificate: UnknownIssuer`, `SELF_SIGNED_CERT_IN_CHAIN`). Compose passes the host bundle at `/etc/corp-ca/ca-bundle.pem` as the `ca_bundle` build secret — share `/etc/corp-ca` in Docker Desktop's file sharing settings. Point `CORP_CA_BUNDLE` at a different path if yours differs. Off the corporate network the secret is optional and builds work without it.

The backend also needs that bundle **at runtime**: completing a Google login exchanges the authorization code over a server-side HTTPS call, and build secrets do not survive into the image. Compose therefore bind-mounts the same file to `/etc/ssl/certs/corp-ca-bundle.pem` and points `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, and `NODE_EXTRA_CA_CERTS` at it. Without it the callback fails with `CERTIFICATE_VERIFY_FAILED: self-signed certificate in certificate chain` and the browser lands back on `/signin` with no session.

## Run everything

```bash
docker compose up
```

- Studio UI: http://localhost:3000
- API: http://localhost:8082
- Health: http://localhost:8082/health/
- Django admin: http://localhost:8082/admin/ (login: `admin` / `secretpassword!` after `docker compose up`)
- Postgres on the host: `localhost:5433`

`localhost` and `127.0.0.1` are different sites to a browser, so the studio calls the API on whichever spelling you opened, and both are allowed CORS origins. Do not mix them by hand — a page on one and an API on the other drops the `SameSite=Lax` session cookie and every call returns 401.

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

Django admin (`/admin/`) accepts Google Workspace login and a local username/password. Compose creates `admin` / `secretpassword!` on startup (same as ehr-bridge). Studio Google users stay out until a superuser grants **Staff status** (and Superuser if they should manage users). Without that, admin explains they are not authorized.
