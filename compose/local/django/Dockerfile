# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.13 \
    PYTHON_TAG=slim \
    PYTHON_TAG_SUFFIX=bookworm \
    BUILD_ENVIRONMENT=local

########
# BASE #
########

FROM python:${PYTHON_VERSION}-${PYTHON_TAG}-${PYTHON_TAG_SUFFIX} AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /usr/local/bin/uv

#########
# BUILD #
#########

FROM base AS build

ARG BUILD_ENVIRONMENT
ENV BUILD_ENVIRONMENT=${BUILD_ENVIRONMENT} \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN --mount=type=cache,target=/var/lib/apt,id=apt-build \
    --mount=type=cache,target=/var/cache/apt,id=apt-build \
    apt-get update \
    && apt-get install --no-install-recommends -y \
        build-essential \
        libpq-dev

COPY pyproject.toml uv.lock /tmp/project/

# ca_bundle: compose passes host /etc/corp-ca/ca-bundle.pem so uv trusts corp TLS
# interception. Optional so this image still builds off the corporate network.
# Runtime deps only: dev/test tooling stays on the host.
RUN --mount=type=secret,id=ca_bundle,required=false \
    --mount=type=cache,target=/root/.cache/uv,id=uv-build \
    bash <<'EOF'
set -euo pipefail

if [[ -s /run/secrets/ca_bundle ]]; then
    export SSL_CERT_FILE=/run/secrets/ca_bundle
    export REQUESTS_CA_BUNDLE=/run/secrets/ca_bundle
fi

cd /tmp/project
uv sync --locked --no-default-groups
cd /

rm -rf /tmp/project
EOF

#######
# RUN #
#######

FROM base

ARG APP_HOME=/app \
    BUILD_ENVIRONMENT

ENV BUILD_ENV=${BUILD_ENVIRONMENT} \
    PATH="/opt/venv/bin:$PATH" \
    VIRTUAL_ENV=/opt/venv \
    DJANGO_SETTINGS_MODULE=config.settings.local \
    PYTHONPATH=${APP_HOME} \
    PUPPETEER_SKIP_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium \
    MERMAID_PUPPETEER_CONFIG=/app/compose/local/django/puppeteer-config.json

WORKDIR ${APP_HOME}

RUN addgroup --system django \
    && adduser --system --ingroup django --home /home/django django \
    && mkdir -p /home/django \
    && chown -R django:django /home/django

RUN --mount=type=secret,id=ca_bundle,required=false \
    --mount=type=cache,target=/var/lib/apt,id=apt-run \
    --mount=type=cache,target=/var/cache/apt,id=apt-run \
    bash <<'EOF'
set -euo pipefail

apt-get update
apt-get install --no-install-recommends -y \
    libpq-dev \
    chromium \
    fonts-liberation \
    nodejs \
    npm

if [[ -s /run/secrets/ca_bundle ]]; then
    export NODE_EXTRA_CA_CERTS=/run/secrets/ca_bundle
fi

npm install -g @mermaid-js/mermaid-cli@11.4.2
npm cache clean --force
EOF

COPY --from=build /opt/venv /opt/venv

COPY --chown=django:django --chmod=755 ./compose/local/django/start /start
COPY --chown=django:django ./compose/local/django/puppeteer-config.json /app/compose/local/django/puppeteer-config.json
COPY --chown=django:django manage.py ${APP_HOME}/
COPY --chown=django:django config ${APP_HOME}/config
COPY --chown=django:django studio ${APP_HOME}/studio

RUN mkdir -p ${APP_HOME}/staticfiles && chown django:django ${APP_HOME}/staticfiles

USER django

EXPOSE 8082

# Backend image is independently runnable. It must not include the SvelteKit app.
CMD ["/start"]
