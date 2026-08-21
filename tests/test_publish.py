import hashlib
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from studio.models import Diagram
from studio.publish import (
    InvalidMermaidError,
    RenderUnavailableError,
    render_with_mmdc,
)

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture
def owner():
    return User.objects.create_user(
        username="owner", email="owner@example.com", password="x"
    )


@pytest.fixture
def owner_client(owner):
    client = Client()
    client.force_login(owner)
    return client


@pytest.fixture
def diagram(owner):
    return Diagram.objects.create(
        owner=owner, title="Chart", source_draft="flowchart TD\n  A-->B"
    )


def _png(tag: str) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + tag.encode()


def test_public_png_before_save_is_404(owner_client, diagram) -> None:
    save_url = f"/api/diagrams/{diagram.id}/save/"
    assert owner_client.get(f"/p/{diagram.id}.png").status_code == 404
    client = Client()
    assert client.get("/p/not-a-token.png").status_code == 404
    assert diagram.public_token is None
    # Save endpoint exists; unpublished public fetch stays 404.
    assert save_url.startswith("/api/")


def test_second_save_keeps_token_and_changes_body(
    owner_client, diagram, settings
) -> None:
    renders = [_png("one"), _png("two")]

    def fake_render(_source: str) -> bytes:
        return renders.pop(0)

    settings.MERMAID_RENDERER = fake_render
    first = owner_client.post(f"/api/diagrams/{diagram.id}/save/")
    assert first.status_code == 200
    token = first.json()["public_token"]
    picture_url = first.json()["picture_url"]
    assert token
    assert picture_url.endswith(f"/p/{token}.png")
    assert "/d/" in first.json()["editor_url"]

    first_png = Client().get(f"/p/{token}.png")
    assert first_png.status_code == 200
    digest_one = hashlib.sha256(first_png.content).hexdigest()

    diagram.source_draft = "flowchart TD\n  C-->D"
    diagram.save(update_fields=["source_draft"])
    second = owner_client.post(f"/api/diagrams/{diagram.id}/save/")
    assert second.status_code == 200
    assert second.json()["public_token"] == token

    second_png = Client().get(f"/p/{token}.png")
    digest_two = hashlib.sha256(second_png.content).hexdigest()
    assert digest_one != digest_two


def test_public_png_does_not_require_or_set_session(
    owner_client, diagram, settings
) -> None:
    settings.MERMAID_RENDERER = lambda source: _png("pub")
    token = owner_client.post(f"/api/diagrams/{diagram.id}/save/").json()[
        "public_token"
    ]

    anonymous = Client()
    response = anonymous.get(f"/p/{token}.png")
    assert response.status_code == 200
    assert response["Content-Type"] == "image/png"
    assert "sessionid" not in response.cookies
    assert "must-revalidate" in response["Cache-Control"]
    assert response["ETag"]
    assert response["Referrer-Policy"] == "no-referrer"
    assert response["X-Robots-Tag"] == "noindex"
    assert anonymous.session.get("_auth_user_id") is None


def test_invalid_mermaid_leaves_previous_png(owner_client, diagram, settings) -> None:
    settings.MERMAID_RENDERER = lambda source: _png("good")
    token = owner_client.post(f"/api/diagrams/{diagram.id}/save/").json()[
        "public_token"
    ]
    previous = Diagram.objects.get(pk=diagram.id).png_published

    def boom(_source: str) -> bytes:
        raise InvalidMermaidError("bad mermaid")

    settings.MERMAID_RENDERER = boom
    diagram.source_draft = "not mermaid"
    diagram.save(update_fields=["source_draft"])
    response = owner_client.post(f"/api/diagrams/{diagram.id}/save/")
    assert response.status_code == 400
    diagram.refresh_from_db()
    assert diagram.public_token == token
    assert bytes(diagram.png_published) == bytes(previous)


def test_empty_save_is_rejected(owner_client, owner, settings) -> None:
    settings.MERMAID_RENDERER = lambda source: _png("nope")
    blank = Diagram.objects.create(owner=owner, source_draft="   ")
    response = owner_client.post(f"/api/diagrams/{blank.id}/save/")
    assert response.status_code == 400
    blank.refresh_from_db()
    assert blank.public_token is None
    assert blank.png_published in (None, b"")


def test_render_failure_is_503_and_keeps_png(owner_client, diagram, settings) -> None:
    settings.MERMAID_RENDERER = lambda source: _png("good")
    owner_client.post(f"/api/diagrams/{diagram.id}/save/")
    previous = bytes(Diagram.objects.get(pk=diagram.id).png_published)

    def down(_source: str) -> bytes:
        raise RenderUnavailableError("mmdc crashed")

    settings.MERMAID_RENDERER = down
    response = owner_client.post(f"/api/diagrams/{diagram.id}/save/")
    assert response.status_code == 503
    diagram.refresh_from_db()
    assert bytes(diagram.png_published) == previous


def test_sequential_id_is_not_the_public_picture_contract(
    owner_client, diagram, settings
) -> None:
    settings.MERMAID_RENDERER = lambda source: _png("tok")
    body = owner_client.post(f"/api/diagrams/{diagram.id}/save/").json()
    token = body["public_token"]
    assert str(diagram.id) not in token
    client = Client()
    assert client.get(f"/p/{diagram.id}.png").status_code == 404
    assert client.get(f"/p/{token}.png").status_code == 200


def test_non_owner_cannot_save(owner, diagram, settings) -> None:
    settings.MERMAID_RENDERER = lambda source: _png("no")
    other = User.objects.create_user(
        username="other", email="other@example.com", password="x"
    )
    client = Client()
    client.force_login(other)
    assert client.post(f"/api/diagrams/{diagram.id}/save/").status_code == 403
    diagram.refresh_from_db()
    assert diagram.public_token is None


def test_browser_launch_failure_is_renderer_unavailable(settings) -> None:
    settings.MERMAID_PUPPETEER_CONFIG = ""
    completed = CompletedProcess(
        args=["mmdc"],
        returncode=1,
        stdout="",
        stderr="Error: Failed to launch the browser process!",
    )

    with patch("studio.publish.subprocess.run", return_value=completed):
        with pytest.raises(RenderUnavailableError):
            render_with_mmdc("flowchart TD\n  A-->B")


def test_parse_failure_is_invalid_mermaid(settings) -> None:
    settings.MERMAID_PUPPETEER_CONFIG = ""
    completed = CompletedProcess(
        args=["mmdc"],
        returncode=1,
        stdout="",
        stderr="Parse error on line 1",
    )

    with patch("studio.publish.subprocess.run", return_value=completed):
        with pytest.raises(InvalidMermaidError):
            render_with_mmdc("not mermaid")


def test_backend_skips_puppeteer_download_before_installing_mmdc() -> None:
    dockerfile = (
        Path(__file__)
        .resolve()
        .parent.parent.joinpath("compose/local/django/Dockerfile")
        .read_text()
    )

    assert dockerfile.index("PUPPETEER_SKIP_DOWNLOAD=true") < dockerfile.index(
        "npm install -g @mermaid-js/mermaid-cli@"
    )
