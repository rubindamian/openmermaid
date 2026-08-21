from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from studio.auth import csrf_bootstrap
from studio.views import health

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("health/", health, name="health"),
    path("auth/csrf/", csrf_bootstrap, name="csrf-bootstrap"),
    path("auth/", include("social_django.urls", namespace="social")),
    path("", include("studio.urls")),
]
