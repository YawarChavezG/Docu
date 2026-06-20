"""
audit_log.py — Router para consultar el registro de auditoria (EPICA 9 - US-9.05).

El audit_log es append-only desde el punto de vista de la API: solo lectura.
La escritura se hace desde `app.core.audit.write_audit()` instrumentado en
los routers de gerencias, areas, configuracion_global, feriados, etc.

Filtros soportados:
  - usuario_id (int)
  - usuario_username (str, exacto)
  - accion (str, exacto)
  - recurso (str, exacto)
  - recurso_id (int)
  - exitoso (bool)
  - desde / hasta (ISO 8601)
  - limit (default 50, max 200)
  - offset (default 0)
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_eto_or_admin
from app.core.audit import write_audit
from app.core.excel_export import build_excel, build_csv
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogOut, AuditLogPaginado

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/audit-log", response_model=AuditLogPaginado)
async def listar_audit_log(
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario_id: Optional[int] = Query(None, description="ID del usuario que ejecuto la accion"),
    usuario_username: Optional[str] = Query(None, description="Username exacto"),
    accion: Optional[str] = Query(None, description="CREATE, UPDATE, DELETE, LOGIN, EXPORT, SYNC, etc."),
    recurso: Optional[str] = Query(None, description="gerencia, area, configuracion_global, etc."),
    recurso_id: Optional[int] = Query(None, description="ID del recurso afectado"),
    exitoso: Optional[bool] = Query(None, description="True=exitosos, False=fallidos"),
    desde: Optional[datetime] = Query(None, description="ISO 8601, ej: 2026-06-01T00:00:00"),
    hasta: Optional[datetime] = Query(None, description="ISO 8601, ej: 2026-06-15T23:59:59"),
    limit: int = Query(50, ge=1, le=200, description="Tamano de pagina (max 200)"),
    offset: int = Query(0, ge=0, description="Desplazamiento"),
):
    """
    Lista entradas del audit-log ordenadas por fecha DESC.
    Solo accesible para ETO o ADMIN.
    """
    await require_eto_or_admin(request, db)

    condiciones = []

    if usuario_id is not None:
        condiciones.append(AuditLog.usuario_id == usuario_id)
    if usuario_username:
        condiciones.append(AuditLog.usuario_username == usuario_username)
    if accion:
        condiciones.append(AuditLog.accion == accion.upper())
    if recurso:
        condiciones.append(AuditLog.recurso == recurso)
    if recurso_id is not None:
        condiciones.append(AuditLog.recurso_id == recurso_id)
    if exitoso is not None:
        condiciones.append(AuditLog.exitoso == exitoso)
    if desde is not None:
        condiciones.append(AuditLog.created_at >= desde)
    if hasta is not None:
        condiciones.append(AuditLog.created_at <= hasta)

    where_clause = and_(*condiciones) if condiciones else None

    count_stmt = select(func.count(AuditLog.id))
    if where_clause is not None:
        count_stmt = count_stmt.where(where_clause)
    total = (await db.execute(count_stmt)).scalar_one()

    items_stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    if where_clause is not None:
        items_stmt = items_stmt.where(where_clause)
    items = (await db.execute(items_stmt)).scalars().all()

    return AuditLogPaginado(
        total=total,
        limit=limit,
        offset=offset,
        items=[AuditLogOut.model_validate(it) for it in items],
    )


@router.get("/audit-log/export")
async def export_audit_log(
    request: Request,
    formato: str = Query("xlsx", pattern="^(xlsx|csv)$"),
    usuario_id: Optional[int] = Query(None),
    usuario_username: Optional[str] = Query(None),
    accion: Optional[str] = Query(None),
    recurso: Optional[str] = Query(None),
    recurso_id: Optional[int] = Query(None),
    exitoso: Optional[bool] = Query(None),
    desde: Optional[datetime] = Query(None),
    hasta: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Exporta el audit log a XLSX (default) o CSV con la misma paleta pastel
    que el export de usuarios. Cap max: 10.000 filas.
    Solo ETO o ADMIN.
    """
    user = await require_eto_or_admin(request, db)

    condiciones = []
    if usuario_id is not None:
        condiciones.append(AuditLog.usuario_id == usuario_id)
    if usuario_username:
        condiciones.append(AuditLog.usuario_username == usuario_username)
    if accion:
        condiciones.append(AuditLog.accion == accion.upper())
    if recurso:
        condiciones.append(AuditLog.recurso == recurso)
    if recurso_id is not None:
        condiciones.append(AuditLog.recurso_id == recurso_id)
    if exitoso is not None:
        condiciones.append(AuditLog.exitoso == exitoso)
    if desde is not None:
        condiciones.append(AuditLog.created_at >= desde)
    if hasta is not None:
        condiciones.append(AuditLog.created_at <= hasta)
    where_clause = and_(*condiciones) if condiciones else None

    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10_000)
    if where_clause is not None:
        stmt = stmt.where(where_clause)
    rows = (await db.execute(stmt)).scalars().all()

    # ─── Construir filas ───
    import json
    from datetime import timezone, timedelta
    bolivia_tz = timezone(timedelta(hours=-4))
    excel_rows: list[list] = []
    for r in rows:
        # Formato fecha Bolivia (UTC-4) para que se vea natural al usuario
        try:
            fecha_bo = r.created_at.astimezone(bolivia_tz).strftime("%d/%m/%Y %H:%M")
        except Exception:
            fecha_bo = r.created_at.isoformat() if r.created_at else ""
        antes = r.detalles.get("antes") if r.detalles else None
        despues = r.detalles.get("despues") if r.detalles else None
        excel_rows.append([
            fecha_bo,
            r.accion,
            r.recurso,
            r.recurso_id or "",
            r.usuario_username or "",
            r.usuario_nombre or "",
            r.descripcion or "",
            (r.ip or ""),
            "SI" if r.exitoso else "NO",
            r.error_msg or "",
            json.dumps(antes, ensure_ascii=False) if antes else "",
            json.dumps(despues, ensure_ascii=False) if despues else "",
        ])

    headers = [
        "Fecha (BO)", "Acción", "Recurso", "Recurso ID", "Username", "Nombre",
        "Descripción", "IP", "Exitoso", "Error", "Valor anterior (JSON)", "Valor nuevo (JSON)",
    ]
    total_row = ["TOTAL", f"{len(excel_rows)} entradas", "", "", "", "", "", "", "", "", "", ""]

    if formato == "xlsx":
        file_bytes = build_excel(
            headers=headers,
            rows=excel_rows,
            sheet_name="Audit Log",
            title=f"Audit Log — COFAR SGD (generado por {user.username})",
            total_row=total_row,
            column_alignments={1: "center", 3: "center", 8: "center"},
        )
        filename = f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        await write_audit(
            db, request, user,
            accion="EXPORT", recurso="audit_log", recurso_id=None,
            descripcion=f"Export de {len(excel_rows)} entradas a XLSX",
            detalles={"formato": "xlsx", "total": len(excel_rows), "filtros": {"accion": accion, "recurso": recurso}},
        )
        await db.commit()
        return Response(
            content=file_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    # CSV
    file_bytes = build_csv(headers=headers, rows=excel_rows, total_row=total_row)
    filename = f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    await write_audit(
        db, request, user,
        accion="EXPORT", recurso="audit_log", recurso_id=None,
        descripcion=f"Export de {len(excel_rows)} entradas a CSV",
        detalles={"formato": "csv", "total": len(excel_rows), "filtros": {"accion": accion, "recurso": recurso}},
    )
    await db.commit()
    return Response(
        content=file_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
