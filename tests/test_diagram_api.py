import json

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from studio.models import Diagram

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture
def owner(db):
    return User.objects.create_user(
        username="owner", email="owner@example.com", password="x"
    )


@pytest.fixture
def other(db):
    return User.objects.create_user(
        username="other", email="other@example.com", password="x"
    )


@pytest.fixture
def owner_client(owner):
    client = Client()
    client.force_login(owner)
    return client


def test_owner_me_returns_email(owner_client, owner) -> None:
    response = owner_client.get("/api/me/")
    assert response.status_code == 200
    assert response.json()["email"] == owner.email


def test_create_and_list_diagrams(owner_client, owner) -> None:
    created = owner_client.post(
        "/api/diagrams/",
        data=json.dumps({"title": "Flow"}),
        content_type="application/json",
    )
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "Flow"
    assert body["source_draft"] == ""
    assert body["source_published"] == ""
    assert body["public_token"] is None
    assert body["id"]

    listed = owner_client.get("/api/diagrams/")
    assert listed.status_code == 200
    assert len(listed.json()["diagrams"]) == 1
    assert listed.json()["diagrams"][0]["id"] == body["id"]
    assert Diagram.objects.filter(owner=owner).count() == 1


def test_owner_reopens_last_draft_not_published(owner_client) -> None:
    created = owner_client.post(
        "/api/diagrams/", data="{}", content_type="application/json"
    )
    diagram_id = created.json()["id"]
    diagram = Diagram.objects.get(pk=diagram_id)
    diagram.source_published = "flowchart TD\n  A-->B"
    diagram.save(update_fields=["source_published"])

    patched = owner_client.patch(
        f"/api/diagrams/{diagram_id}/",
        data=json.dumps({"source_draft": "flowchart TD\n  X-->Y"}),
        content_type="application/json",
    )
    assert patched.status_code == 200
    assert patched.json()["source_draft"] == "flowchart TD\n  X-->Y"
    assert patched.json()["source_published"] == "flowchart TD\n  A-->B"

    reopened = owner_client.get(f"/api/diagrams/{diagram_id}/")
    assert reopened.status_code == 200
    assert reopened.json()["source_draft"] == "flowchart TD\n  X-->Y"
    assert reopened.json()["source_published"] == "flowchart TD\n  A-->B"
    diagram.refresh_from_db()
    assert diagram.source_published == "flowchart TD\n  A-->B"
    assert diagram.png_published in (None, b"")


def test_anonymous_owner_api_is_401() -> None:
    client = Client()
    assert client.get("/api/me/").status_code == 401
    assert client.get("/api/diagrams/").status_code == 401
    assert (
        client.post(
            "/api/diagrams/", data="{}", content_type="application/json"
        ).status_code
        == 401
    )
    assert "flowchart" not in client.get("/api/diagrams/").content.decode()


def test_non_owner_gets_403(owner, other, owner_client) -> None:
    created = owner_client.post(
        "/api/diagrams/", data="{}", content_type="application/json"
    )
    diagram_id = created.json()["id"]
    owner_client.patch(
        f"/api/diagrams/{diagram_id}/",
        data=json.dumps({"source_draft": "secret draft"}),
        content_type="application/json",
    )

    other_client = Client()
    other_client.force_login(other)
    detail = other_client.get(f"/api/diagrams/{diagram_id}/")
    assert detail.status_code == 403
    assert "secret draft" not in detail.content.decode()

    patched = other_client.patch(
        f"/api/diagrams/{diagram_id}/",
        data=json.dumps({"source_draft": "hijack"}),
        content_type="application/json",
    )
    assert patched.status_code == 403
    assert Diagram.objects.get(pk=diagram_id).source_draft == "secret draft"


def test_owner_list_does_not_include_other_users_diagrams(owner_client, other) -> None:
    Diagram.objects.create(owner=other, title="Not yours", source_draft="private")
    listed = owner_client.get("/api/diagrams/")
    assert listed.json()["diagrams"] == []
