import hashlib

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from studio.models import Diagram

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


def test_public_get_before_first_save_is_404(owner) -> None:
    diagram = Diagram.objects.create(owner=owner, source_draft="flowchart TD\n  A-->B")
    client = Client()
    assert client.get("/p/missing-token.png").status_code == 404
    assert client.get(f"/p/{diagram.id}.png").status_code == 404


def test_etag_matches_png_digest(owner_client, owner, settings) -> None:
    diagram = Diagram.objects.create(owner=owner, source_draft="flowchart TD\n  A-->B")
    payload = b"\x89PNG\r\n\x1a\nETagMe"
    settings.MERMAID_RENDERER = lambda source: payload
    token = owner_client.post(f"/api/diagrams/{diagram.id}/save/").json()[
        "public_token"
    ]
    response = Client().get(f"/p/{token}.png")
    expected = hashlib.sha256(payload).hexdigest()
    assert response["ETag"] == f'"{expected}"'
    not_modified = Client().get(f"/p/{token}.png", HTTP_IF_NONE_MATCH=f'"{expected}"')
    assert not_modified.status_code == 304
