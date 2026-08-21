"""
With these settings, tests run faster.
"""

from .base import *  # noqa: F401, F403
from .base import DATABASES, INSTALLED_APPS, MIDDLEWARE, env

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="test-insecure-secret-key-not-for-production",
)
DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
TEST_RUNNER = "django.test.runner.DiscoverRunner"

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

DATABASES["default"].update(
    {
        "CONN_MAX_AGE": 0,
        "CONN_HEALTH_CHECKS": False,
    }
)

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    }
}

MIDDLEWARE = [mw for mw in MIDDLEWARE if "whitenoise" not in mw]

if "debug_toolbar" in INSTALLED_APPS:
    INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "debug_toolbar"]

if "debug_toolbar.middleware.DebugToolbarMiddleware" in MIDDLEWARE:
    MIDDLEWARE = [
        mw
        for mw in MIDDLEWARE
        if mw != "debug_toolbar.middleware.DebugToolbarMiddleware"
    ]
