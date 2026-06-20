"""
Tareas de Celery (placeholder).
Las tareas reales se completarán en R1:
- reasignar_tareas_vencidas (cron 23:59)
- actualizar_vigencia_vencida (cron 23:59)
- sincronizar_ad (cada 6h)
- enviar_email_bienvenida
- generar_pdf_caratula
"""
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.hello")
def hello(name: str = "world") -> str:
    """Tarea de prueba. Se elimina cuando se agreguen las tareas reales."""
    return f"Hello, {name}!"
