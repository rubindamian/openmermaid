from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
@transaction.non_atomic_requests
def health(_request):
    """Unauthenticated liveness probe for Compose and independent backend deploys."""
    return JsonResponse({"status": "ok"})
