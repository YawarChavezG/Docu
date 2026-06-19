"""
Celery application instance.
Inicialización del broker Redis + result backend.
Las tareas se registran en app/workers/tasks.py (futuro).
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# ─── Celery instance ───
celery_app = Celery(
    "cofar_sgd",
    broker=settings.celery_broker_url or settings.redis_url,
    backend=settings.celery_result_backend or settings.redis_url,
    include=[
        "app.workers.tasks",
    ],
)

# ─── Config ───
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.tz,
    enable_utc=True,
    task_acks_late=True,  # no perder tareas si el worker se cae
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# ─── Schedule (cron jobs) ───
# En R1 se completarán las tareas reales. Por ahora placeholders.
celery_app.conf.beat_schedule = {
    # Sesion 23 / Bloque B2: desactivar ausencias vencidas (00:05)
    "desactivar-ausencias-vencidas": {
        "task": "app.workers.tasks.desactivar_ausencias_vencidas",
        "schedule": crontab(hour=0, minute=5),  # 00:05 hrs todos los dias
    },
    # "sla-timeout-check": {
    #     "task": "app.workers.tasks.reasignar_tareas_vencidas",
    #     "schedule": crontab(hour=23, minute=59),
    # },
    # "vigencia-vencida-check": {
    #     "task": "app.workers.tasks.actualizar_vigencia_vencida",
    #     "schedule": crontab(hour=23, minute=59),
    # },
    # Sesion 33 (deploy v1.1.0-qas): activar sync AD cada 6 horas.
    # Si LDAP_ENABLED=false, la task skip con warning (no rompe el beat).
    "sync-ad": {
        "task": "app.workers.tasks.sincronizar_ad",
        "schedule": crontab(hour="*/6"),  # cada 6 horas
    },
}
