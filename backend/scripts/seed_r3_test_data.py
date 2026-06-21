"""
Seed de datos de prueba para R3 - Workflow completo.
Crea 4 documentos en distintos estados del flujo con tareas y timeline.
"""
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.usuario import Usuario, usuario_roles
from app.models.rol import Rol, CodigoRol
from app.models.documento import Documento, EstatusDocumento, VigenciaDocumento
from app.models.documento_flujo import DocumentoFlujo, TipoSolicitud
from app.models.tarea import Tarea
from app.models.bitacora_timeline import BitacoraTimeline


async def main():
    async with AsyncSessionLocal() as db:
        usuarios = (await db.execute(
            select(Usuario).limit(10)
        )).scalars().all()
        if not usuarios:
            print("No hay usuarios en BD")
            return

        # Encontrar ETO sin lazy load
        eto = usuarios[0]
        for u in usuarios:
            r = await db.execute(
                select(usuario_roles).where(usuario_roles.c.usuario_id == u.id)
            )
            role_ids = [row.rol_id for row in r.all()]
            if role_ids:
                rr = await db.execute(select(Rol.codigo).where(Rol.id.in_(role_ids)))
                if any(row[0] == CodigoRol.ETO for row in rr.all()):
                    eto = u; break

        otros = [u for u in usuarios if u.id != eto.id][:5]

        from app.models.area import Area
        area_q = await db.execute(select(Area).limit(1))
        area = area_q.scalar_one_or_none()
        if not area:
            print("No hay areas"); return

        from app.models.tipo_documento import TipoDocumento
        tipo_q = await db.execute(select(TipoDocumento).limit(1))
        tipo = tipo_q.scalar_one_or_none()
        if not tipo:
            print("No hay tipos"); return

    base = datetime.now(timezone.utc) - timedelta(days=5)

    # ESCENARIO A: Documento en LIBERACION_ETO (esperando ETO)
    doc_a = Documento(
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        correlativo=1001, codigo="PRO-5-1001", version="00",
        titulo="Procedimiento de Control de Calidad - Lote 1001",
        vigencia=VigenciaDocumento.VIGENTE, estatus=EstatusDocumento.LIBERACION_ETO, activo=True,
    )
    db.add(doc_a); await db.flush()
    flujo_a = DocumentoFlujo(
        documento_id=doc_a.id, tipo_solicitud=TipoSolicitud.CREACION,
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        codigo_snapshot="PRO-5-1001", version_snapshot="00",
        titulo="Procedimiento de Control de Calidad",
        elaborador_id=otros[0].id if otros else eto.id, cargo_elaborador="Analista",
        fecha_solicitud=base, revisor_ids=[u.id for u in otros[:3]],
        aprobador_ids=[u.id for u in otros[3:5]],
    )
    db.add(flujo_a); await db.flush()
    nodo = BitacoraTimeline(
        documento_flujo_id=flujo_a.id, usuario_id=otros[0].id if otros else eto.id,
        accion="CREADO", color_nodo="azul",
        estado_origen="EN_ELABORACION", estado_destino="LIBERACION_ETO",
        created_at=base,
    )
    db.add(nodo)

    # ESCENARIO B: Documento EN_REVISION (con tareas para revisores)
    doc_b = Documento(
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        correlativo=1002, codigo="INS-6-1002", version="00",
        titulo="Instructivo de Mantenimiento de Equipos - Planta Baja",
        vigencia=VigenciaDocumento.VIGENTE, estatus=EstatusDocumento.EN_REVISION, activo=True,
    )
    db.add(doc_b); await db.flush()
    flujo_b = DocumentoFlujo(
        documento_id=doc_b.id, tipo_solicitud=TipoSolicitud.CREACION,
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        codigo_snapshot="INS-6-1002", version_snapshot="00",
        titulo="Instructivo de Mantenimiento de Equipos",
        elaborador_id=otros[1].id if len(otros) > 1 else eto.id, cargo_elaborador="Tecnico",
        fecha_solicitud=base - timedelta(days=2), revisor_ids=[u.id for u in otros[:3]],
        aprobador_ids=[u.id for u in otros[3:5]],
    )
    db.add(flujo_b); await db.flush()
    for i, uid in enumerate(otros[:3]):
        t = Tarea(documento_flujo_id=flujo_b.id, usuario_id=uid, tipo_tarea="REVISION",
                  estado="PENDIENTE", fecha_asignacion=base - timedelta(days=2))
        db.add(t)
        if i == 1:
            tm = BitacoraTimeline(documento_flujo_id=flujo_b.id, usuario_id=uid,
                                  accion="PENDIENTE", color_nodo="ambar",
                                  created_at=base - timedelta(days=2))
            db.add(tm)
    # Timeline del flujo B
    base_b = base - timedelta(days=2)
    for acc, col, d in [("CREADO", "azul", 0), ("LIBERADO_ETO", "verde", 1)]:
        n = BitacoraTimeline(documento_flujo_id=flujo_b.id, usuario_id=eto.id,
                            accion=acc, color_nodo=col,
                            created_at=base_b + timedelta(hours=d))
        db.add(n)

    # ESCENARIO C: Documento EN_CORRECCION (1 revisor rechazo, esperando correccion)
    doc_c = Documento(
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        correlativo=1003, codigo="MAN-10-1003", version="00",
        titulo="Manual de Usuario - Sistema de Gestion Documental",
        vigencia=VigenciaDocumento.VIGENTE, estatus=EstatusDocumento.EN_REVISION, activo=True,
    )
    db.add(doc_c); await db.flush()
    flujo_c = DocumentoFlujo(
        documento_id=doc_c.id, tipo_solicitud=TipoSolicitud.CREACION,
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        codigo_snapshot="MAN-10-1003", version_snapshot="00",
        titulo="Manual de Usuario SGD",
        elaborador_id=otros[2].id if len(otros) > 2 else eto.id, cargo_elaborador="Analista",
        fecha_solicitud=base - timedelta(days=5), revisor_ids=[u.id for u in otros[:3]],
        aprobador_ids=[u.id for u in otros[3:5]],
    )
    db.add(flujo_c); await db.flush()
    base_c = base - timedelta(days=5)
    for acc, col, d in [("CREADO", "azul", 0), ("LIBERADO_ETO", "verde", 1)]:
        n = BitacoraTimeline(documento_flujo_id=flujo_c.id, usuario_id=eto.id,
                            accion=acc, color_nodo=col,
                            created_at=base_c + timedelta(hours=d))
        db.add(n)
    # R1 aprueba, R2 rechaza, R3 aprueba
    for i, uid in enumerate(otros[:3]):
        est = "RECHAZADO" if i == 1 else "COMPLETADO"
        t = Tarea(documento_flujo_id=flujo_c.id, usuario_id=uid, tipo_tarea="REVISION",
                  estado=est, fecha_asignacion=base_c + timedelta(days=1),
                  fecha_completado=base_c + timedelta(days=2) if est == "COMPLETADO" else None,
                  observacion="Corregir la seccion de roles de usuario, no coincide con el manual de procesos" if est == "RECHAZADO" else None)
        db.add(t)
    accs = [("APROBADO", "verde"), ("RECHAZADO", "rojo"), ("APROBADO", "verde")]
    for (acc, col), uid in zip(accs, otros[:3]):
        n = BitacoraTimeline(documento_flujo_id=flujo_c.id, usuario_id=uid,
                            accion=acc, color_nodo=col, created_at=base_c + timedelta(days=2),
                            observacion="Corregir seccion roles" if acc == "RECHAZADO" else None)
        db.add(n)

    # ESCENARIO D: Documento APROBADO (flujo completo exitoso)
    doc_d = Documento(
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        correlativo=1004, codigo="MET-1-1004", version="00",
        titulo="Metodologia de Evaluacion de Proveedores",
        vigencia=VigenciaDocumento.VIGENTE, estatus=EstatusDocumento.APROBADO, activo=True,
    )
    db.add(doc_d); await db.flush()
    flujo_d = DocumentoFlujo(
        documento_id=doc_d.id, tipo_solicitud=TipoSolicitud.CREACION,
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        codigo_snapshot="MET-1-1004", version_snapshot="00",
        titulo="Metodologia de Evaluacion de Proveedores",
        elaborador_id=otros[0].id if otros else eto.id, cargo_elaborador="Analista Sr.",
        fecha_solicitud=base - timedelta(days=10), revisor_ids=[u.id for u in otros[:3]],
        aprobador_ids=[u.id for u in otros[3:5]],
    )
    db.add(flujo_d); await db.flush()
    base_d = base - timedelta(days=10)
    secuencia = [
        ("CREADO", "azul", 0), ("LIBERADO_ETO", "verde", 1),
        ("APROBADO", "verde", 3), ("APROBADO", "verde", 4),
        ("APROBADO", "verde", 4), ("PUBLICADO", "verde", 5),
    ]
    for acc, col, d in secuencia:
        n = BitacoraTimeline(documento_flujo_id=flujo_d.id, usuario_id=eto.id,
                            accion=acc, color_nodo=col,
                            created_at=base_d + timedelta(days=d))
        db.add(n)

        await db.commit()

    print(f"Seed completado: 3 documentos en distintos estados del flujo documental")
    print(f"  A: LIBERACION_ETO - flujo_id={flujo.id} '{doc.titulo[:40]}'")
    print(f"  B: EN_REVISION - flujo_id={flujo2.id} '{doc2.titulo[:40]}' (3 tareas pendientes)")
    print(f"  C: APROBADO - flujo_id={flujo3.id} '{doc3.titulo[:40]}' (timeline completo)")


if __name__ == "__main__":
    asyncio.run(main())
