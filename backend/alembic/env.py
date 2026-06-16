"""
Alembic env.py — COFAR SGD
Configura el engine desde app.core.config.settings (lee DATABASE_URL).
Importa todos los modelos para que Alembic los detecte en autogenerate.
"""
import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ─── Make 'app' importable ───
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.core.database import Base  # noqa: E402

# ─── Importar TODOS los modelos para que Alembic los detecte ───
# (Alembic hace `metadata = Base.metadata` y compara todas las tablas)
from app.models.rol import Rol  # noqa: E402,F401
from app.models.gerencia import Gerencia  # noqa: E402,F401
from app.models.area import Area  # noqa: E402,F401
from app.models.usuario import Usuario, usuario_roles, usuario_modulos  # noqa: E402,F401
from app.models.modulo import Modulo  # noqa: E402,F401
from app.models.delegacion import Delegacion  # noqa: E402,F401
from app.models.ausencia import Ausencia  # noqa: E402,F401
from app.models.firma_digital import FirmaDigital  # noqa: E402,F401
from app.models.log_sync_ad import LogSyncAd  # noqa: E402,F401
from app.models.configuracion_global import ConfiguracionGlobal  # noqa: E402,F401
from app.models.feriado import Feriado  # noqa: E402,F401
from app.models.email_template import EmailTemplate  # noqa: E402,F401

# ─── Alembic Config ───
config = context.config

# Sobreescribir sqlalchemy.url con la URL real del config
config.set_main_option("sqlalchemy.url", settings.database_url)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (genera SQL sin conectar)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
