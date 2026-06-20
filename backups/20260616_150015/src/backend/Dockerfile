# ════════════════════════════════════════════════════════════════
# Backend — Python 3.12 slim (Debian Bookworm)
# Multi-stage para imagen final pequeña
# ════════════════════════════════════════════════════════════════

# ─── Stage 1: builder (instala deps en un virtualenv) ───
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencias del sistema para compilar wheels (WeasyPrint, ldap, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    libffi-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements primero (caché de Docker)
COPY requirements/ /app/requirements/

# Crear venv e instalar
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements/base.txt

# ─── Stage 2: runtime (imagen final pequeña) ───
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Solo las librerías de runtime (sin compiladores)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libldap-2.5-0 \
    libsasl2-2 \
    libssl3 \
    libffi8 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar el venv del builder
COPY --from=builder /opt/venv /opt/venv

# Copiar el código
COPY . /app

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 sgduser && \
    mkdir -p /app/storage /app/logs && \
    chown -R sgduser:sgduser /app
USER sgduser

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Por defecto: uvicorn con hot-reload (desarrollo)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
