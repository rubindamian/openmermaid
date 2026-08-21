# syntax=docker/dockerfile:1.7

FROM node:22-bookworm-slim

WORKDIR /app

COPY package.json package-lock.json ./

ENV NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false \
    NPM_CONFIG_AUDIT=false

# ca_bundle: same corp TLS bundle the backend build uses. Optional so this image
# still builds off the corporate network.
RUN --mount=type=secret,id=ca_bundle,required=false \
    bash <<'EOF'
set -euo pipefail

if [[ -s /run/secrets/ca_bundle ]]; then
    export NODE_EXTRA_CA_CERTS=/run/secrets/ca_bundle
fi

npm ci --no-audit --no-fund
EOF

COPY . .

ENV PUBLIC_API_ORIGIN=http://localhost:8082
RUN npm run build

ENV NODE_ENV=production \
    PORT=3000 \
    HOST=0.0.0.0 \
    ORIGIN=http://localhost:3000 \
    PUBLIC_API_ORIGIN=http://localhost:8082

EXPOSE 3000

# Independently runnable. Talks to the API only via PUBLIC_API_ORIGIN.
USER node
CMD ["node", "build"]
