import json
from functools import wraps
from uuid import UUID

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from studio.models import Diagram, new_public_token
from studio.publish import InvalidMermaidError, RenderUnavailableError, render_png


def require_session(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required."}, status=401)
        return view(request, *args, **kwargs)

    return wrapped


def _picture_url(diagram: Diagram) -> str | None:
    if not diagram.public_token:
        return None
    origin = settings.PUBLIC_API_ORIGIN.rstrip("/")
    return f"{origin}/p/{diagram.public_token}.png"


def _editor_path(diagram: Diagram) -> str:
    return f"/d/{diagram.id}"


def serialize_diagram(diagram: Diagram) -> dict:
    return {
        "id": str(diagram.id),
        "title": diagram.title,
        "source_draft": diagram.source_draft,
        "source_published": diagram.source_published,
        "public_token": diagram.public_token,
        "picture_url": _picture_url(diagram),
        "editor_url": _editor_path(diagram),
        "saved_at": diagram.saved_at.isoformat() if diagram.saved_at else None,
        "updated_at": diagram.updated_at.isoformat() if diagram.updated_at else None,
    }


def _json_body(request) -> tuple[dict | None, JsonResponse | None]:
    if not request.body:
        return {}, None
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, JsonResponse({"detail": "Invalid JSON."}, status=400)
    if not isinstance(payload, dict):
        return None, JsonResponse({"detail": "JSON object required."}, status=400)
    return payload, None


def _get_owned(request, diagram_id: str) -> tuple[Diagram | None, JsonResponse | None]:
    try:
        UUID(str(diagram_id))
    except ValueError:
        return None, JsonResponse({"detail": "Not found."}, status=404)
    try:
        diagram = Diagram.objects.get(pk=diagram_id)
    except Diagram.DoesNotExist:
        return None, JsonResponse({"detail": "Not found."}, status=404)
    if diagram.owner_id != request.user.id:
        return None, JsonResponse({"detail": "Forbidden."}, status=403)
    return diagram, None


@require_session
@require_GET
def me(request):
    return JsonResponse(
        {
            "id": request.user.id,
            "email": request.user.email,
            "username": request.user.get_username(),
        }
    )


@require_session
@require_http_methods(["GET", "POST"])
def diagram_collection(request):
    if request.method == "GET":
        diagrams = Diagram.objects.filter(owner=request.user)
        return JsonResponse({"diagrams": [serialize_diagram(d) for d in diagrams]})

    payload, error = _json_body(request)
    if error:
        return error
    title = str(payload.get("title") or "Untitled")[:255]
    source_draft = str(payload.get("source_draft") or "")
    diagram = Diagram.objects.create(
        owner=request.user, title=title, source_draft=source_draft
    )
    return JsonResponse(serialize_diagram(diagram), status=201)


@require_session
@require_http_methods(["GET", "PATCH"])
def diagram_detail(request, diagram_id: str):
    diagram, error = _get_owned(request, diagram_id)
    if error:
        return error
    if request.method == "GET":
        return JsonResponse(serialize_diagram(diagram))

    payload, error = _json_body(request)
    if error:
        return error
    update_fields = ["updated_at"]
    if "title" in payload:
        diagram.title = str(payload["title"] or "Untitled")[:255]
        update_fields.append("title")
    if "source_draft" in payload:
        diagram.source_draft = str(payload["source_draft"] or "")
        update_fields.append("source_draft")
    diagram.save(update_fields=update_fields)
    diagram.refresh_from_db()
    return JsonResponse(serialize_diagram(diagram))


@require_session
@require_http_methods(["POST"])
def diagram_save(request, diagram_id: str):
    diagram, error = _get_owned(request, diagram_id)
    if error:
        return error
    source = (diagram.source_draft or "").strip()
    if not source:
        return JsonResponse({"detail": "Source is empty."}, status=400)
    try:
        png = render_png(source)
    except InvalidMermaidError as exc:
        return JsonResponse(
            {"detail": str(exc) or "Invalid Mermaid source."}, status=400
        )
    except RenderUnavailableError as exc:
        return JsonResponse({"detail": str(exc) or "Render failed."}, status=503)
    if not diagram.public_token:
        diagram.public_token = new_public_token()
    diagram.source_published = diagram.source_draft
    diagram.png_published = png
    diagram.saved_at = timezone.now()
    diagram.save(
        update_fields=[
            "public_token",
            "source_published",
            "png_published",
            "saved_at",
            "updated_at",
        ]
    )
    diagram.refresh_from_db()
    return JsonResponse(serialize_diagram(diagram))
