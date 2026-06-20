"""
Configuración de base de datos (SQLAlchemy 2.0 async).
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM."""
    pass


# ─── Engine (pool de conexiones) ───
# SQLite (tests) NO acepta pool_size/max_overflow; PostgreSQL (prod) sí.
_engine_kwargs: dict = {
    "echo": settings.debug,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
}
if not settings.database_url.startswith("sqlite"):
    _engine_kwargs["pool_size"] = 10
    _engine_kwargs["max_overflow"] = 20

engine = create_async_engine(settings.database_url, **_engine_kwargs)

# ─── Session factory ───
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency para inyectar sesión de DB en endpoints."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
