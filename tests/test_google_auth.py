from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from social_core.backends.google import GoogleOAuth2
from social_django.models import UserSocialAuth

pytestmark = pytest.mark.django_db

User = get_user_model()

ALLOWED_USERINFO = {
    "sub": "google-sub-allowed",
    "email": "ada@example.com",
    "hd": "example.com",
    "email_verified": True,
    "given_name": "Ada",
    "family_name": "Lovelace",
    "name": "Ada Lovelace",
}

OUTSIDE_HD_USERINFO = {
    **ALLOWED_USERINFO,
    "sub": "google-sub-outside",
    "email": "ada@evil.example",
    "hd": "evil.example",
}

EMAIL_MATCHES_ALLOWLIST_WITHOUT_HD = {
    **ALLOWED_USERINFO,
    "sub": "google-sub-no-hd",
    "email": "ada@example.com",
}
EMAIL_MATCHES_ALLOWLIST_WITHOUT_HD.pop("hd")


def _complete_google(client: Client, userinfo: dict):
    def fake_auth_complete(self, *args, **kwargs):
        response = {**userinfo, "access_token": "test-token"}
        kwargs.update({"response": response, "backend": self})
        return self.strategy.authenticate(*args, **kwargs)

    with patch.object(GoogleOAuth2, "auth_complete", fake_auth_complete):
        return client.get("/auth/complete/google-oauth2/")


def test_login_url_rejects_get() -> None:
    client = Client()
    response = client.get(reverse("social:begin", args=["google-oauth2"]))
    assert response.status_code == 405
    assert User.objects.count() == 0


def test_csrf_bootstrap_sets_cookie_and_returns_token() -> None:
    client = Client()
    response = client.get("/auth/csrf/")
    assert response.status_code == 200
    body = response.json()
    assert body["csrfToken"]
    assert "csrftoken" in response.cookies


def test_allowed_hd_creates_user_keyed_by_google_sub(settings) -> None:
    settings.GOOGLE_WORKSPACE_DOMAINS = ["example.com"]
    client = Client()
    response = _complete_google(client, ALLOWED_USERINFO)

    assert response.status_code == 302
    assert response["Location"] == f"{settings.FRONTEND_ORIGIN}/"
    assert User.objects.count() == 1
    social = UserSocialAuth.objects.get()
    assert social.uid == "google-sub-allowed"
    assert social.user.email == "ada@example.com"
    assert client.session.get("_auth_user_id") == str(social.user.pk)


def test_disallowed_hd_creates_no_user(settings) -> None:
    settings.GOOGLE_WORKSPACE_DOMAINS = ["example.com"]
    client = Client()
    response = _complete_google(client, OUTSIDE_HD_USERINFO)

    assert User.objects.count() == 0
    assert UserSocialAuth.objects.count() == 0
    assert not client.session.get("_auth_user_id")
    assert response.status_code in {302, 403}


def test_missing_hd_is_rejected_even_when_email_matches_allowlist(settings) -> None:
    settings.GOOGLE_WORKSPACE_DOMAINS = ["example.com"]
    client = Client()
    _complete_google(client, EMAIL_MATCHES_ALLOWLIST_WITHOUT_HD)

    assert User.objects.count() == 0
    assert UserSocialAuth.objects.count() == 0


def test_cancelled_oauth_creates_no_user() -> None:
    client = Client()
    response = client.get("/auth/complete/google-oauth2/", {"error": "access_denied"})
    assert User.objects.count() == 0
    assert UserSocialAuth.objects.count() == 0
    assert response.status_code in {302, 400, 403}


def test_login_post_redirects_to_google(settings) -> None:
    settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = "test-client-id"
    settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = "test-secret"
    client = Client(enforce_csrf_checks=True)
    csrf = client.get("/auth/csrf/").json()["csrfToken"]
    response = client.post(
        reverse("social:begin", args=["google-oauth2"]),
        HTTP_X_CSRFTOKEN=csrf,
    )
    assert response.status_code == 302
    location = response["Location"]
    parsed = urlparse(location)
    assert parsed.netloc == "accounts.google.com"
    params = parse_qs(parsed.query)
    assert params["hd"] == ["example.com"]
    assert "openid" in params["scope"][0]
