from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import Client

from config.settings.base import loopback_origins

ROOT = Path(__file__).resolve().parent.parent


def test_django_check() -> None:
    call_command("check")


def test_health_returns_ok_without_session() -> None:
    client = Client()
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "sessionid" not in response.cookies
    assert response.wsgi_request.user.is_anonymous


def test_postgres_engine_is_configured() -> None:
    engine = settings.DATABASES["default"]["ENGINE"]
    assert engine == "django.db.backends.postgresql"


def test_frontend_origin_drives_cors_and_csrf() -> None:
    assert settings.FRONTEND_ORIGIN
    assert settings.FRONTEND_ORIGIN in settings.CORS_ALLOWED_ORIGINS
    assert settings.FRONTEND_ORIGIN in settings.CSRF_TRUSTED_ORIGINS
    assert settings.SESSION_COOKIE_SAMESITE == "Lax"
    assert settings.SESSION_COOKIE_HTTPONLY is True
    assert settings.SESSION_COOKIE_SECURE is False


def test_both_loopback_spellings_are_allowed_origins() -> None:
    # A browser on 127.0.0.1 must not get a CORS-blocked response that the UI
    # can only report as an unreachable API.
    assert loopback_origins("http://localhost:3000") == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    assert loopback_origins("http://127.0.0.1:3000") == [
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]
    assert loopback_origins("https://studio.example.com") == [
        "https://studio.example.com"
    ]
    assert "http://127.0.0.1:3000" in settings.CORS_ALLOWED_ORIGINS
    assert "http://127.0.0.1:3000" in settings.CSRF_TRUSTED_ORIGINS
    assert "127.0.0.1:3000" in settings.SOCIAL_AUTH_ALLOWED_REDIRECT_HOSTS
    # Admin lives on the API origin; Google `next=/admin/` must be allowed back.
    assert "localhost:8082" in settings.SOCIAL_AUTH_ALLOWED_REDIRECT_HOSTS
    assert "127.0.0.1:8082" in settings.SOCIAL_AUTH_ALLOWED_REDIRECT_HOSTS


def test_compose_starts_frontend_backend_and_postgres_independently() -> None:
    compose = (ROOT / "docker-compose.yml").read_text()
    assert "\n  backend:" in compose
    assert "\n  postgres:" in compose
    assert "\n  frontend:" in compose
    assert "compose/local/django/Dockerfile" in compose
    assert "compose/local/frontend/Dockerfile" in compose
    assert '"8082:8082"' in compose
    assert '"5433:5432"' in compose
    assert '"3000:3000"' in compose
    frontend_block = compose.split("\n  frontend:", 1)[1].split("\n  postgres:", 1)[0]
    assert "depends_on" not in frontend_block
    backend_block = compose.split("\n  backend:", 1)[1].split("\n  frontend:", 1)[0]
    assert "frontend" not in backend_block


def test_backend_dockerfile_excludes_frontend_app() -> None:
    dockerfile = (ROOT / "compose/local/django/Dockerfile").read_text()
    assert "COPY --chown=django:django studio" in dockerfile
    assert (
        "frontend" not in dockerfile.lower()
        or "must not include the sveltekit app" in dockerfile.lower()
    )
    dockerignore = (ROOT / ".dockerignore").read_text()
    assert "frontend" in dockerignore


def test_local_start_bootstraps_the_compose_superuser() -> None:
    start = (ROOT / "compose/local/django/start").read_text()
    assert "ensure_superuser" in start
    assert "secretpassword!" in start
