"""
main.py — Punto de entrada FastAPI
"""
import logging
import os
import time
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.core.config import settings
from app.api.v1 import auth, health, admin_impersonate, usuarios, gerencias, areas, configuracion_global

# ─── Timezone (Bolivia = UTC-4) ───
# Truco: pisamos el converter CLASS-attribute de logging.Formatter con
# uno que devuelve la hora de Bolivia. Asi TODOS los formatters (incluso
# los que crea uvicorn/sqlalchemy DESPUES) usaran esta conversion.
os.environ.setdefault("TZ", "America/La_Paz")

_BOLIVIA_OFFSET_HOURS = -4  # UTC-4


def _bolivia_converter(secs: float) -> time.struct_time:
    """Converter que devuelve la hora de Bolivia (UTC-4) como struct_time."""
    return time.gmtime(secs + _BOLIVIA_OFFSET_HOURS * 3600)


# Aplicar a la clase para que formatters NUEVOS ya usen Bolivia
logging.Formatter.converter = staticmethod(_bolivia_converter)


def _patch_existing_formatters() -> None:
    """Pisa el converter en formatters ya instanciados (uvicorn, sqlalchemy)."""
    for handler in logging.getLogger().handlers:
        if handler.formatter is not None:
            handler.formatter.converter = staticmethod(_bolivia_converter)
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access",
                        "sqlalchemy", "sqlalchemy.engine"):
        lg = logging.getLogger(logger_name)
        for h in lg.handlers:
            if h.formatter is not None:
                h.formatter.converter = staticmethod(_bolivia_converter)


# ─── Logging setup ───
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)
# Re-pisar formatters que basicConfig acaba de crear
_patch_existing_formatters()

logger = logging.getLogger(__name__)


# ─── App ───
app = FastAPI(
    title="COFAR SGD API",
    description="Sistema de Gestión Documental — COFAR SRL",
    version=__version__,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# ─── CORS ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,  # importante para cookies HttpOnly
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-CSRF-Token"],  # para que el frontend pueda leerlo
)


# ─── Startup / Shutdown ───
@app.on_event("startup")
async def startup_event():
    # Re-pisar formatters por si uvicorn creo handlers nuevos durante el arranque
    _patch_existing_formatters()

    logger.info(f"🚀 COFAR SGD API v{__version__} iniciando...")
    logger.info(f"   Environment: {settings.environment}")
    logger.info(f"   Debug: {settings.debug}")
    logger.info(f"   CORS origins: {settings.cors_origins}")
    logger.info(f"   Timezone: America/La_Paz (UTC-4)")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 COFAR SGD API cerrando...")


# ─── Routers ───
app.include_router(health.router, prefix=settings.api_v1_prefix, tags=["Health"])
app.include_router(auth.router, prefix=settings.api_v1_prefix, tags=["Auth"])
app.include_router(usuarios.router, prefix=settings.api_v1_prefix, tags=["Usuarios"])
app.include_router(gerencias.router, prefix=settings.api_v1_prefix, tags=["Gerencias"])
app.include_router(areas.router, prefix=settings.api_v1_prefix, tags=["Areas"])
app.include_router(configuracion_global.router, prefix=settings.api_v1_prefix, tags=["Configuracion"])
app.include_router(admin_impersonate.router, prefix=settings.api_v1_prefix)


# ─── Root ───
@app.get("/")
async def root():
    return {
        "service": "cofar-sgd-api",
        "version": __version__,
        "environment": settings.environment,
        "docs": "/docs" if settings.debug else None,
    }
