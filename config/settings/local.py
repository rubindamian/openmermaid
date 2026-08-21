from .base import *  # noqa: F401, F403
from .base import INSTALLED_APPS, MIDDLEWARE, env

# GENERAL
# ------------------------------------------------------------------------------
DEBUG = True
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="local-insecure-secret-key-not-for-production",
)
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "backend", "0.0.0.0"]

# Session cookies stay insecure on local HTTP. Production sets Secure.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# WhiteNoise
# ------------------------------------------------------------------------------
INSTALLED_APPS = ["whitenoise.runserver_nostatic"] + INSTALLED_APPS

# django-debug-toolbar (optional; installed via the dev dependency group)
# ------------------------------------------------------------------------------
if env.bool("DJANGO_DEBUG_TOOLBAR", default=True):
    try:
        import debug_toolbar  # noqa: F401
    except ImportError:
        pass
    else:
        INSTALLED_APPS += ["debug_toolbar"]
        MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

INTERNAL_IPS = ["127.0.0.1"]
if env("USE_DOCKER", default="no") == "yes":
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]

# django-extensions
# ------------------------------------------------------------------------------
try:
    import django_extensions  # noqa: F401
except ImportError:
    pass
else:
    INSTALLED_APPS += ["django_extensions"]
