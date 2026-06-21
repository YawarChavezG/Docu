"""
Script demo: Puebla bitacora_timeline con escenarios variados para validacion frontend.
Correr: docker exec -it sgd-backend python scripts/seed_timeline_demo.py
"""
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.bitacora_timeline import BitacoraTimeline
from app.models.documento_flujo import DocumentoFlujo
from app.models.usuario import Usuario
from app.models.documento import Documento, EstatusDocumento
from app.services.timeline_service import escribir_bitacora


async def main():
    db: AsyncSession = await anext(get_db())

    # Buscar un flujo existente
    flujo = (await db.execute(
        select(DocumentoFlujo).limit(1)
    )).scalar_one_or_none()

    if not flujo:
        print("No hay flujos en BD. Crea un documento primero.")
        return

    doc = (await db.execute(
        select(Documento).where(Documento.id == flujo.documento_id)
    )).scalar_one_or_none()

    # Buscar usuario ETO
    user = (await db.execute(
        select(Usuario).limit(1)
    )).scalar_one_or_none()
    if not user:
        print("No hay usuarios")
        return

    # Limpiar timeline previo
    await db.execute(
        BitacoraTimeline.__table__.delete().where(
            BitacoraTimeline.documento_flujo_id == flujo.id
        )
    )

    # ESCENARIO: Flujo real con 3 revisores (R1 aprueba, R2 observa, R3 aprueba)
    # Fechas escalonadas para simular paso del tiempo
    base = datetime.now(timezone.utc)
    pasos = [
        (0, "CREADO", "EN_ELABORACION", "LIBERACION_ETO", "azul",
         f"Documento {doc.codigo_completo} creado por {user.nombre_completo}" if doc else "Documento creado"),
        (2, "LIBERADO_ETO", "LIBERACION_ETO", "EN_REVISION", "verde",
         f"Documento liberado por ETO {user.nombre_completo}"),
        # R1 aprueba (tarea 101)
        (5, "APROBADO", "EN_REVISION", "EN_APROBACION", "verde",
         "Aprobado por Revisor 1"),
        # R2 observa (tarea 102)
        (7, "RECHAZADO", "EN_REVISION", "EN_CORRECCION", "rojo",
         "Observacion: Corregir seccion 3.2 - Los tiempos de respuesta no coinciden con el anexo A."),
        # R3 aprueba (tarea 103)
        (10, "APROBADO", "EN_REVISION", "EN_APROBACION", "verde",
         "Aprobado por Revisor 3"),
        # Correccion enviada por solicitante
        (14, "CORREGIDO", "EN_CORRECCION", "EN_REVISION", "azul",
         "Secciones 3.2 y 4.1 corregidas segun observaciones de Revisor 2"),
        # Bypass: vuelve solo a R2
        (17, "APROBADO", "EN_REVISION", "EN_APROBACION", "verde",
         "Aprobado por Revisor 2 (correccion validada)"),
        # Pasa a aprobacion
        (20, "PENDIENTE", "EN_APROBACION", "EN_APROBACION", "ambar",
         "Tarea de aprobacion asignada a Aprobador 1"),
        (22, "APROBADO", "EN_APROBACION", "APROBADO", "verde",
         "Aprobado por Aprobador 1"),
        (25, "PUBLICADO", "APROBADO", "VIGENTE", "verde",
         "Documento publicado en Lista Maestra"),
    ]
    for minutos, accion, origen, destino, color, obs in pasos:
        ts = base + timedelta(minutes=minutos)
        # Crear nodo con created_at manual (forzando la fecha)
        nodo = BitacoraTimeline(
            documento_flujo_id=flujo.id,
            usuario_id=user.id,
            accion=accion,
            estado_origen=origen,
            estado_destino=destino,
            color_nodo=color,
            observacion=obs,
            created_at=ts,
        )
        db.add(nodo)

    await db.commit()
    print(f"✅ Timeline sembrado para flujo_id={flujo.id}")
    print(f"   Total nodos: {len(pasos)}")
    print(f"   Acciones: {', '.join(p[0] for p in pasos)}")


if __name__ == "__main__":
    asyncio.run(main())
