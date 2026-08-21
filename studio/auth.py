"""Google Workspace login helpers for python-social-auth."""

from __future__ import annotations

import json
from base64 import urlsafe_b64decode
from typing import Any

from django.conf import settings
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from social_core.exceptions import AuthForbidden


def hosted_domain_from_google_response(response: dict[str, Any]) -> str | None:
    """Return the Workspace hosted domain from userinfo or the ID-token `hd` claim."""
    hd = response.get("hd")
    if hd:
        return str(hd).strip().lower()

    id_token = response.get("id_token")
    if not id_token or not isinstance(id_token, str):
        return None
    parts = id_token.split(".")
    if len(parts) < 2:
        return None
    payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        payload = json.loads(urlsafe_b64decode(payload_b64.encode("ascii")))
    except (ValueError, json.JSONDecodeError):
        return None
    token_hd = payload.get("hd")
    if not token_hd:
        return None
    return str(token_hd).strip().lower()


def allowed_workspace_domains() -> set[str]:
    return {
        d.strip().lower()
        for d in settings.GOOGLE_WORKSPACE_DOMAINS
        if d and str(d).strip()
    }


def enforce_google_hosted_domain(backend, response, *args, **kwargs):
    """Reject Google accounts whose ID-token `hd` is missing or not allowlisted.

    Email domain is not sufficient: Google can mint addresses that look on-domain
    without a matching Workspace `hd` claim.
    """
    if backend.name != "google-oauth2":
        return
    hd = hosted_domain_from_google_response(response)
    allowed = allowed_workspace_domains()
    if not hd or hd not in allowed:
        raise AuthForbidden(backend)


@require_GET
@ensure_csrf_cookie
def csrf_bootstrap(_request):
    """Set the CSRF cookie on the API origin and return the token for X-CSRFToken."""
    token = get_token(_request)
    return JsonResponse({"csrfToken": token})
