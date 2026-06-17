"""
tests/conftest.py — Fixtures compartidos para pytest.

Estrategia: SQLite in-memory asincrónico via aiosqlite + Base.metadata.create_all.
Las cookies de auth (session, user_id) se setean directamente en el test client.
"""
from __future__ import annotations

import asyncio
import os
import sys
from typing import AsyncGenerator, Optional

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ─── Path setup ──────────────────────────────────────────────────────
# Permitir imports absolutos tipo `from app.xxx import yyy`
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ─── Forzar SQLite in-memory para tests (antes de importar app.*) ───
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["LDAP_ENABLED"] = "false"
os.environ["SMTP_ENABLED"] = "false"
os.environ["GRAPH_ENABLED"] = "false"
os.environ["DEBUG"] = "false"
os.environ["ENVIRONMENT"] = "test"

# Importar los modelos para que Base.metadata los registre ANTES de create_all.
# Pero NO importamos `app.core.database` (que crea el engine contra la URL
# de settings); lo importamos después de monkeypatch.
from app.models.rol import CodigoRol, Rol  # noqa: E402
from app.models.modulo import CodigoModulo, Modulo  # noqa: E402
from app.models.usuario import EstadoUsuario, EstadoDelegacion, Usuario  # noqa: E402
from app.models.gerencia import Gerencia  # noqa: E402
from app.models.area import Area  # noqa: E402
from app.models.tipo_documento import TipoDocumento  # noqa: E402
from app.models.estado import Estado  # noqa: E402
from app.models.email_template import EmailTemplate  # noqa: E402
from app.models.feriado import Feriado  # noqa: E402
from app.models.matriz_enrutamiento_eto import MatrizEnrutamientoEto  # noqa: E402
from app.models.configuracion_global import ConfiguracionGlobal  # noqa: E402
from app.models.audit_log import AuditLog  # noqa: E402
# R2 sesion 21: modelos nuevos
from app.models.documento import (  # noqa: E402
    Documento,
    VigenciaDocumento,
    EstatusDocumento,
)
from app.models.documento_flujo import (  # noqa: E402
    DocumentoFlujo,
    TipoSolicitud,
)
from app.models.archivo_adjunto import (  # noqa: E402
    ArchivoAdjunto,
    TipoAdjunto,
    StorageBackend as StorageBackendAdjunto,
)
from app.models.semaforizacion_tarea import SemaforizacionTarea  # noqa: E402

from app.core.database import Base  # noqa: E402
from app.core import database as db_module  # noqa: E402

# ─── Test engine + session factory ───────────────────────────────────
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
)

# SQLite no tiene hashtext() ni pg_try_advisory_xact_lock(). Registramos
# stubs para que los servicios que usan advisory locks (correlativo_service)
# funcionen en tests. La implementacion es deterministica y serial: para el
# mismo key, siempre devuelve el mismo "lock" (que es solo un valor cualquiera).
import hashlib


def _sqlite_hashtext(s) -> int:
    """Stub de Postgres hashtext(). Devuelve un int32 deterministico.
    Acepta str o bytes porque SQLite puede pasarle cualquiera."""
    if isinstance(s, bytes):
        s = s.decode("utf-8")
    h = hashlib.md5(s.encode("utf-8")).hexdigest()
    # Primeros 8 chars como int (32 bits, mismo rango que hashtext)
    return int(h[:8], 16) & 0x7FFFFFFF


def _sqlite_pg_try_advisory_xact_lock(key) -> int:
    """Stub de pg_try_advisory_xact_lock(). En SQLite los tests son single-thread,
    asi que siempre devuelve 1 (true)."""
    return 1


from sqlalchemy import event


@event.listens_for(test_engine.sync_engine, "connect")
def _register_sqlite_functions(dbapi_conn, connection_record):
    """Registra hashtext y pg_try_advisory_xact_lock como funciones SQLite."""
    dbapi_conn.create_function("hashtext", 1, _sqlite_hashtext)
    dbapi_conn.create_function("pg_try_advisory_xact_lock", 1, _sqlite_pg_try_advisory_xact_lock)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Monkeypatch: hacer que el `engine` y `AsyncSessionLocal` del modulo
# `app.core.database` apunten al test_engine. Asi el `get_db()` que
# importan los routers (vía `from app.core.database import get_db`)
# retorna sesiones de test.
db_module.engine = test_engine
db_module.AsyncSessionLocal = TestSessionLocal

# Importar la app DESPUES del monkeypatch.
from app.main import app  # noqa: E402


# ─── Module-scoped setup: crear tablas una vez ───────────────────────
@pytest_asyncio.fixture(scope="session", autouse=True)
async def _setup_database():
    """Crea todas las tablas en la BD de test al inicio de la sesion."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()


# ─── Function-scoped fixtures: per-test cleanup ─────────────────────
@pytest_asyncio.fixture(autouse=True)
async def _truncate_tables(db_session):
    """Limpia todas las tablas despues de cada test.

    Depende de db_session para que pytest asigure que se ejecute DESPUES
    de seed_catalogos y de los tests que usan la sesion.
    """
    yield

    # Commit explicito: hace visibles los `db_session.add()` que el test hizo
    try:
        await db_session.commit()
    except Exception:
        await db_session.rollback()

    # Cleanup
    async with TestSessionLocal() as session:
        try:
            for tbl in reversed(Base.metadata.sorted_tables):
                await session.execute(tbl.delete())
            await session.commit()
        except Exception:
            await session.rollback()

    # Rollback en la sesion del test (si quedo transaccion abierta)
    try:
        await db_session.rollback()
    except Exception:
        pass


# ─── Test client (httpx async contra FastAPI app) ───────────────────
@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ─── Seed catalogos (5 roles, 11 modulos, 1 admin, 1 ETO) ────────────
@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
        await session.commit()


@pytest_asyncio.fixture
async def seed_catalogos(db_session: AsyncSession):
    """Inserta los catalogos base (5 roles, 11 modulos, 1 admin, 1 ETO, 1 gerencia, 1 area)."""
    # Roles
    roles_data = [
        (CodigoRol.ADMIN, "Administrador", "Acceso total", False),
        (CodigoRol.ETO, "ETO", "Parametrizacion y liberacion", False),
        (CodigoRol.ELABORADOR_REVISOR, "Elaborador - Revisor", "Crea y revisa docs", True),
        (CodigoRol.ELABORADOR_REVISOR_APROBADOR, "Elaborador - Revisor - Aprobador", "Crea, revisa y aprueba", True),
        (CodigoRol.VISUALIZADOR_CL_EVAL, "Visualizador (CL-EVAL)", "Solo lectura", False),
    ]
    roles = {}
    for codigo, nombre, desc, req_delegado in roles_data:
        rol = Rol(codigo=codigo, nombre=nombre, descripcion=desc, requiere_delegado=req_delegado)
        db_session.add(rol)
        roles[codigo] = rol
    await db_session.flush()

    # Modulos
    modulos_data = [
        (CodigoModulo.TODOS, "Todos", "Bypass RBAC"),
        ("BANDEJA_TAREAS", "Bandeja de Tareas", "Bandeja centralizada"),
        ("LISTA_MAESTRA", "Lista Maestra", "Lista maestra de documentos"),
        ("MIS_EVAL", "Mis Evaluaciones", "Evaluaciones y controles de lectura"),
        ("ASISTENTE_IA", "Asistente IA", "Chat con IA"),
        ("NUEVA_SOLICITUD", "Nueva Solicitud", "Wizard de creacion"),
        ("CONSULTAR_DOC", "Consultar Documentos", "Consulta de docs"),
        ("PLANTILLAS_DOC", "Plantillas Documentales", "Plantillas"),
        ("MI_BANDEJA", "Mi Bandeja", "Bandeja personal"),
        ("PARAMETRIZACION", "Parametrizacion General", "Solo ETO/ADMIN"),
        ("BANDEJA_PARAMETROS", "Parametros Bandeja", "Semaforizacion"),
    ]
    modulos = {}
    for codigo, nombre, desc in modulos_data:
        mod = Modulo(codigo=codigo, nombre=nombre, descripcion=desc)
        db_session.add(mod)
        modulos[codigo] = mod
    await db_session.flush()

    # 1 gerencia + 1 area
    ger = Gerencia(sigla="CAL", nombre="CALIDAD", orden=1, activo=True)
    db_session.add(ger)
    await db_session.flush()

    area = Area(gerencia_id=ger.id, sigla="CC", nombre="CONTROL DE CALIDAD", activo=True, orden=1)
    db_session.add(area)
    await db_session.flush()

    # 1 admin y 1 ETO
    admin = Usuario(
        username="admin",
        email="admin@cofar.local",
        nombre_completo="Administrador Test",
        iniciales="AT",
        cargo="Administrador",
        area_id=area.id,
        estado=EstadoUsuario.ACTIVO,
        estado_delegacion=EstadoDelegacion.NA,
        ad_postal_code="00000001",
    )
    admin.roles.append(roles[CodigoRol.ADMIN])
    admin.modulos.append(modulos[CodigoModulo.TODOS])
    db_session.add(admin)

    eto = Usuario(
        username="aromero",
        email="aromero@cofar.local",
        nombre_completo="Aracely Romero",
        iniciales="AR",
        cargo="ETO",
        area_id=area.id,
        estado=EstadoUsuario.ACTIVO,
        estado_delegacion=EstadoDelegacion.NA,
        ad_postal_code="10000001",
    )
    eto.roles.append(roles[CodigoRol.ETO])
    eto.modulos.append(modulos[CodigoModulo.TODOS])
    db_session.add(eto)

    # usuario sin rol
    sin_rol = Usuario(
        username="solicitante",
        email="solicitante@cofar.local",
        nombre_completo="Solicitante Test",
        iniciales="ST",
        cargo="Solicitante",
        area_id=area.id,
        estado=EstadoUsuario.ACTIVO,
        estado_delegacion=EstadoDelegacion.NA,
        ad_postal_code="00000002",
    )
    db_session.add(sin_rol)

    await db_session.commit()
    await db_session.refresh(admin)
    await db_session.refresh(eto)
    await db_session.refresh(sin_rol)

    return {
        "roles": roles,
        "modulos": modulos,
        "gerencia": ger,
        "area": area,
        "admin": admin,
        "eto": eto,
        "sin_rol": sin_rol,
    }


# ─── Auth helpers ────────────────────────────────────────────────────
def _auth_cookies(user_id: int) -> dict:
    """Genera cookies de sesion para un user_id dado."""
    return {
        "session": f"dev-session-{user_id}",
        "user_id": str(user_id),
        "csrf_token": f"dev-csrf-{user_id}",
    }


@pytest.fixture
def auth_eto_cookies(seed_catalogos):
    return _auth_cookies(seed_catalogos["eto"].id)


@pytest.fixture
def auth_admin_cookies(seed_catalogos):
    return _auth_cookies(seed_catalogos["admin"].id)


@pytest.fixture
def auth_sin_rol_cookies(seed_catalogos):
    return _auth_cookies(seed_catalogos["sin_rol"].id)
