"""
Base settings to build other settings files upon.
"""

from pathlib import Path

import environ

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
APPS_DIR = ROOT_DIR / "studio"
env = environ.Env()

READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=True)
if READ_DOT_ENV_FILE:
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        env.read_env(str(env_file))

# GENERAL
# ------------------------------------------------------------------------------
DEBUG = env.bool("DJANGO_DEBUG", False)
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-us"
SITE_ID = 1
USE_I18N = True
USE_TZ = True

# DATABASES
# ------------------------------------------------------------------------------
# Host-side defaults use 5433 so this stack does not collide with ehr-bridge on 5432.
# Compose sets POSTGRES_HOST=postgres and POSTGRES_PORT=5432 (container port).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="openmermaid"),
        "USER": env("POSTGRES_USER", default="postgres"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="password"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5433"),
        "ATOMIC_REQUESTS": True,
        "CONN_MAX_AGE": env.int("CONN_MAX_AGE", default=60),
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# URLS
# ------------------------------------------------------------------------------
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
]
THIRD_PARTY_APPS = [
    "corsheaders",
    "social_django",
]
LOCAL_APPS = [
    "studio.apps.StudioConfig",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# AUTHENTICATION
# ------------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    "social_core.backends.google.GoogleOAuth2",
    "django.contrib.auth.backends.ModelBackend",
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# STATIC
# ------------------------------------------------------------------------------
STATIC_ROOT = str(ROOT_DIR / "staticfiles")
STATIC_URL = "/static/"
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(APPS_DIR / "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

# SECURITY
# ------------------------------------------------------------------------------
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"

# Split-origin browser studio (KTD3). Session cookie lives on the API host.
FRONTEND_ORIGIN = env("FRONTEND_ORIGIN", default="http://localhost:3000")
PUBLIC_API_ORIGIN = env("PUBLIC_API_ORIGIN", default="http://localhost:8082")
CORS_ALLOWED_ORIGINS = [FRONTEND_ORIGIN]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [FRONTEND_ORIGIN]

GOOGLE_CLIENT_ID = env("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = env("GOOGLE_CLIENT_SECRET", default="")
GOOGLE_OAUTH_REDIRECT_URI = env(
    "GOOGLE_OAUTH_REDIRECT_URI",
    default="http://localhost:8082/auth/complete/google-oauth2/",
)
GOOGLE_WORKSPACE_DOMAINS = env.list("GOOGLE_WORKSPACE_DOMAINS", default=["example.com"])

LOGIN_URL = f"{FRONTEND_ORIGIN}/"
LOGIN_REDIRECT_URL = f"{FRONTEND_ORIGIN}/"
LOGOUT_REDIRECT_URL = f"{FRONTEND_ORIGIN}/"
SOCIAL_AUTH_LOGIN_REDIRECT_URL = f"{FRONTEND_ORIGIN}/"
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = f"{FRONTEND_ORIGIN}/"
SOCIAL_AUTH_LOGIN_ERROR_URL = f"{FRONTEND_ORIGIN}/?auth_error=1"
SOCIAL_AUTH_RAISE_EXCEPTIONS = False
SOCIAL_AUTH_SANITIZE_REDIRECTS = True
SOCIAL_AUTH_ALLOWED_REDIRECT_HOSTS = [FRONTEND_ORIGIN.split("://", 1)[-1].split("/")[0]]
SOCIAL_AUTH_JSONFIELD_ENABLED = True
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = GOOGLE_CLIENT_ID
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = GOOGLE_CLIENT_SECRET
SOCIAL_AUTH_GOOGLE_OAUTH2_USE_UNIQUE_USER_ID = True
SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS = {
    "hd": GOOGLE_WORKSPACE_DOMAINS[0] if GOOGLE_WORKSPACE_DOMAINS else "",
    "prompt": "select_account",
}
SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "studio.auth.enforce_google_hosted_domain",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)

# mermaid-cli (mmdc) runs inside the backend image. Tests inject MERMAID_RENDERER.
MERMAID_CLI = env("MERMAID_CLI", default="mmdc")
MERMAID_PUPPETEER_CONFIG = env(
    "MERMAID_PUPPETEER_CONFIG",
    default=str(ROOT_DIR / "compose/local/django/puppeteer-config.json"),
)
MERMAID_RENDER_TIMEOUT = env.int("MERMAID_RENDER_TIMEOUT", default=30)
PUPPETEER_EXECUTABLE_PATH = env("PUPPETEER_EXECUTABLE_PATH", default="")
MERMAID_RENDERER = None

# EMAIL
# ------------------------------------------------------------------------------
MAILERS = {
    "default": {
        "BACKEND": env(
            "DJANGO_EMAIL_BACKEND",
            default="django.core.mail.backends.console.EmailBackend",
        ),
    }
}

# ADMIN
# ------------------------------------------------------------------------------
ADMIN_URL = "admin/"
ADMINS = ["openmermaid@localhost"]
MANAGERS = ADMINS

# LOGGING
# ------------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}
