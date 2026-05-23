# ─────────────────────────────────────────────────────────────────
#  Atlas – Next.js frontend
#
#  Targets:
#    dev   → hot-reload dev server (used by docker-compose)
#    deps  → install deps (shared intermediate)
#    build → production build
#    prod  → minimal standalone runner (~120 MB)
#
#  Build prod image:
#    docker build --target prod -t atlas-frontend .
#
#  The compose file uses the dev target automatically.
# ─────────────────────────────────────────────────────────────────

ARG NODE_VERSION=20-alpine

# ── 1. Install dependencies ───────────────────────────────────────
FROM node:${NODE_VERSION} AS deps

WORKDIR /app

# Copy manifests only so this layer is cached unless deps change
COPY package.json package-lock.json ./

RUN npm ci --prefer-offline


# ── 2. Development server ─────────────────────────────────────────
# Mounted source replaces /app at runtime; node_modules come from
# the deps layer via the named volume in compose.
FROM node:${NODE_VERSION} AS dev

WORKDIR /app

# Copy pre-installed modules into the image so the named volume
# inherits them on first run (compose overwrites /app with the
# bind-mount but preserves the node_modules volume).
COPY --from=deps /app/node_modules ./node_modules

# Also copy package manifests so npm ci works offline if the volume
# wasn't seeded (e.g. bind-mount races on macOS / WSL first boot).
COPY package.json package-lock.json ./

EXPOSE 3000

ENV NODE_ENV=development \
    NEXT_TELEMETRY_DISABLED=1

# Self-healing start: if the named volume landed empty (docker/macOS
# bind-mount ordering quirk) reinstall from the offline npm cache
# before handing off to the dev server.
CMD ["sh", "-c", "[ -x node_modules/.bin/next ] || npm ci --prefer-offline; npm run dev"]


# ── 3. Production build ───────────────────────────────────────────
FROM node:${NODE_VERSION} AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build


# ── 4. Production runner (standalone) ────────────────────────────
FROM node:${NODE_VERSION} AS prod

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# next build --output standalone emits a self-contained server
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static     ./.next/static
COPY --from=builder /app/public           ./public

EXPOSE 3000

# The standalone server entry point
CMD ["node", "server.js"]
