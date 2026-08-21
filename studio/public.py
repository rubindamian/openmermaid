import hashlib

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from studio.models import Diagram

_CACHE = "public, max-age=60, must-revalidate"


@csrf_exempt
@require_GET
def public_png(request, token: str):
    if not token:
        return HttpResponse(status=404)
    try:
        diagram = Diagram.objects.only("png_published", "public_token").get(
            public_token=token
        )
    except Diagram.DoesNotExist:
        return HttpResponse(status=404)
    png = diagram.png_published
    if not png:
        return HttpResponse(status=404)
    body = bytes(png)
    etag = f'"{hashlib.sha256(body).hexdigest()}"'
    if request.headers.get("If-None-Match") == etag:
        response = HttpResponse(status=304)
    else:
        response = HttpResponse(body, content_type="image/png")
    response["ETag"] = etag
    response["Cache-Control"] = _CACHE
    response["Referrer-Policy"] = "no-referrer"
    response["X-Robots-Tag"] = "noindex"
    return response
