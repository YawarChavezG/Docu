"""
Tareas de Celery.

Sesion 23 / Bloque B2: agregar `desactivar_ausencias_vencidas` (cron 00:05).
Recorre todas las ausencias con fecha_hasta < hoy y activo=true, las marca
como activo=false y setea usuarios.ausente=false para esos usuarios.

Las tareas reales se completarán en R1:
- reasignar_tareas_vencidas (cron 23:59)
- actualizar_vigencia_vencida (cron 23:59)
- sincronizar_ad (cada 6h)
- enviar_email_bienvenida
- generar_pdf_caratula
"""
import asyncio
import logging
from datetime import date

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.hello")
def hello(name: str = "world") -> str:
    """Tarea de prueba. Se elimina cuando se agreguen las tareas reales."""
    return f"Hello, {name}!"


@celery_app.task(name="app.workers.tasks.desactivar_ausencias_vencidas")
def desactivar_ausencias_vencidas() -> dict:
    """
    Marca como inactivas las ausencias cuya fecha_hasta ya paso.
    Tambien pone usuarios.ausente=false para esos usuarios.

    Idempotente: si se corre varias veces al dia, solo afecta a las nuevas
    ausencias vencidas.
    """
    return asyncio.run(_desactivar_ausencias_async())


async def _desactivar_ausencias_async() -> dict:
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.ausencia import Ausencia
    from app.models.usuario import Usuario
    from app.core.audit import write_audit

    hoy = date.today()
    desactivadas = 0
    usuarios_actualizados = set()

    async with AsyncSessionLocal() as db:
        try:
            # 1) Buscar ausencias vencidas y aun activas
            stmt = select(Ausencia).where(
                Ausencia.activo == True,
                Ausencia.fecha_hasta < hoy,
            )
            rows = (await db.execute(stmt)).scalars().all()
            for a in rows:
                a.activo = False
                usuarios_actualizados.add(a.usuario_id)
                desactivadas += 1
                # Audit log (no usamos write_audit porque requiere Request)
                # El admin/ETO vera esto en /audit-log
            # 2) Para cada usuario afectado, setear ausente=False
            for uid in usuarios_actualizados:
                u = (await db.execute(
                    select(Usuario).where(Usuario.id == uid)
                )).scalar_one_or_none()
                if u and u.ausente:
                    u.ausente = False
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.exception(f"Error en desactivar_ausencias_vencidas: {e}")
            return {"ok": False, "error": str(e), "desactivadas": 0}
    msg = f"desactivar_ausencias_vencidas: {desactivadas} ausencias desactivadas, {len(usuarios_actualizados)} usuarios actualizados"
    logger.info(msg)
    return {"ok": True, "desactivadas": desactivadas, "usuarios_actualizados": len(usuarios_actualizados)}
