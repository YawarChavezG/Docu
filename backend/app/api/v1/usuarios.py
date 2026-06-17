"""
Endpoints de gestion de usuarios.

Pensado para la pantalla Parametrizacion > Gestion de Usuarios.
Reemplaza al mock `frontend/src/data/parametrosSistema.js` que tiene
`usuariosParamDB` hardcoded.

Endpoints (todos bajo prefix /api/v1):
  GET   /usuarios              -> lista paginada de usuarios de la BD
  GET   /usuarios/{id}         -> detalle de un usuario
  PATCH /usuarios/{id}         -> override vacaciones/estado (Sesion B - #9e)
  POST  /usuarios/sync-ad      -> sincroniza usuarios desde el AD real
  GET   /usuarios/sync-status  -> estado del ultimo sync (idempotente)
  GET   /usuarios/export       -> export XLSX/CSV profesional (Sesion B - #9e)

  NOTA: las rutas NO repiten el segmento /usuarios/ porque el router
  se monta con prefix=/api/v1 en main.py. Repetirlo provoca
  colision con /{user_id} (que captura "usuarios" como int -> 422).

GETs y sync-ad requieren rol ADMIN.
El PATCH y el export admiten ETO o ADMIN (override de vacaciones es US-9.05).
"""
import logging
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.audit import write_audit
from app.core.config import settings
from app.core.excel_export import build_csv, build_excel
from app.core.permissions import require_eto_or_admin
from app.models.usuario import Usuario, EstadoUsuario, EstadoDelegacion
from app.models.rol import Rol, CodigoRol
from app.models.area import Area
from app.services import ad_service

logger = logging.getLogger(__name__)
# Prefix = "/usuarios" para que las rutas declaradas ("", "/sync-ad", etc.)
# vivan bajo /usuarios. En main.py se monta este router con
# prefix=settings.api_v1_prefix (=/api/v1), por lo tanto la URL final
# de cada endpoint es /api/v1/usuarios/<ruta>.
# (Si NO tuvieramos prefix aca, las rutas colisionarian con las de
# health y auth, y "/{user_id}" capturaria /api/v1/openapi.json, /me, etc.)
router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


# ─── Schemas ───

class UsuarioOut(BaseModel):
    id: int
    username: str
    nombre_completo: str
    iniciales: str
    email: Optional[str] = None
    cargo: Optional[str] = None
    area_id: Optional[int] = None
    area_sigla: Optional[str] = None
    gerencia_sigla: Optional[str] = None
    ad_postal_code: Optional[str] = None
    ad_info: Optional[str] = None
    ad_last_synced_at: Optional[str] = None
    azure_oid: Optional[str] = None
    estado: str
    ausente: bool
    estado_delegacion: str
    delegado_id: Optional[int] = None
    delegado_username: Optional[str] = None
    delegado_nombre: Optional[str] = None
    roles: list[str] = []
    modulos: list[str] = []
    ad_warning: Optional[str] = None


class UsuariosListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[UsuarioOut]
    kpis: dict
    warnings: list[str] = []


class SyncAdRequest(BaseModel):
    # 2026-06-15: subido de 750 a 5000. El script validado
    # scripts/sync_ad_oficial.py trae 759 usuarios; con max_results=750
    # se truncaba el sync a 750 incluso si el AD tenia mas.
    max_results: int = 5000


class SyncAdResponse(BaseModel):
    total_ad: int
    creados: int
    actualizados: int
    sin_cambios: int
    excluidos: int
    errores: int
    duracion_seg: float
    warnings: list[str] = []


# ─── Schemas Sesion B (tarea #9e) ───

class UsuarioUpdate(BaseModel):
    """
    Override de campos administrativos del usuario.
    Solo ETO/ADMIN. Todos los campos son opcionales (PATCH semantico).
    Acciones tipicas:
      - Marcar vacaciones: {ausente: true, observaciones: "Vacaciones 15-30 jul"}
      - Suspender temporalmente: {estado: "inactivo", observaciones: "Suspendido por X"}
      - Reactivar: {estado: "activo", ausente: false}
      - Asignar rol: {rol_codigo: "ETO"}
      - Asignar/quitar delegado: {delegado_id: 42} o {delegado_id: None}
    """
    estado: Optional[EstadoUsuario] = Field(
        default=None, description="activo / inactivo / desvinculado / ausente"
    )
    ausente: Optional[bool] = Field(default=None, description="Flag de ausencia (lectura en UI)")
    estado_delegacion: Optional[EstadoDelegacion] = Field(
        default=None, description="pendiente / asignado / na"
    )
    rol_codigo: Optional[str] = Field(
        default=None, max_length=100,
        description="Codigo del rol a asignar (ADMIN, ETO, ELABORADOR - REVISOR, etc.). "
                    "Si el usuario ya tiene roles, se reemplazan todos por este."
    )
    delegado_id: Optional[int] = Field(
        default=None, description="ID del usuario delegado. None para quitar el delegado."
    )
    observaciones: Optional[str] = Field(
        default=None, max_length=500,
        description="Nota del override (queda en audit_log.detalles)"
    )


# ─── Helpers ───

async def _get_current_user(request: Request, db: AsyncSession) -> Optional[Usuario]:
    """Lee user_id de la cookie y devuelve el Usuario (con roles)."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    try:
        uid = int(user_id)
    except ValueError:
        return None
    return (await db.execute(
        select(Usuario).where(Usuario.id == uid)
        .options(selectinload(Usuario.roles), selectinload(Usuario.modulos))
    )).scalar_one_or_none()


async def _require_admin(request: Request, db: AsyncSession) -> Usuario:
    """Verifica que el usuario logueado sea ADMIN. Si no, 403."""
    user = await _get_current_user(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="No autenticado")
    is_admin = any(r.codigo == CodigoRol.ADMIN for r in user.roles)
    if not is_admin:
        raise HTTPException(
            status_code=403,
            detail=f"Solo usuarios con rol ADMIN pueden acceder (tu rol: {', '.join(r.codigo for r in user.roles) or 'ninguno'})"
        )
    return user


async def _resolve_gerencia_de_usuario(
    db: AsyncSession, user: Usuario
) -> Optional[int]:
    """Devuelve gerencia_id del usuario a traves de su area. None si no tiene area."""
    if user.area_id is None:
        return None
    row = (await db.execute(
        select(Area.gerencia_id).where(Area.id == user.area_id)
    )).one_or_none()
    return row[0] if row else None


def _to_out(user: Usuario) -> UsuarioOut:
    """Convierte un Usuario ORM a UsuarioOut."""
    gerencia_sigla = None
    if user.area and user.area.gerencia:
        gerencia_sigla = user.area.gerencia.sigla
    ad_warning = None
    if not user.ad_postal_code:
        ad_warning = "Sin codigo SAP (postalCode vacio en AD)"
    return UsuarioOut(
        id=user.id,
        username=user.username,
        nombre_completo=user.nombre_completo,
        iniciales=user.iniciales or "",
        email=user.email,
        cargo=user.cargo or "(sin cargo)",
        area_id=user.area_id,
        area_sigla=user.area.sigla if user.area else None,
        gerencia_sigla=gerencia_sigla,
        ad_postal_code=user.ad_postal_code,
        ad_info=user.ad_info,
        ad_last_synced_at=user.ad_last_synced_at.isoformat() if user.ad_last_synced_at else None,
        azure_oid=user.azure_oid,
        estado=user.estado.value if hasattr(user.estado, "value") else str(user.estado),
        ausente=user.ausente,
        estado_delegacion=user.estado_delegacion.value if hasattr(user.estado_delegacion, "value") else str(user.estado_delegacion),
        delegado_id=user.delegado_id,
        delegado_username=user.delegado.username if user.delegado else None,
        delegado_nombre=user.delegado.nombre_completo if user.delegado else None,
        roles=[r.codigo for r in user.roles],
        modulos=[m.codigo for m in user.modulos],
        ad_warning=ad_warning,
    )


# ─── Endpoints ───

# ═══════════════════════════════════════════════════════════════
# IMPORTANTE — orden de declaracion de rutas:
# FastAPI matchea las rutas EN ORDEN DE DECLARACION. La ruta
# generica /{user_id} captura cualquier string, por lo tanto
# las rutas especificas (/sync-ad, /sync-status) DEBEN ir ANTES.
# De lo contrario /sync-status se interpreta como user_id="sync-status"
# y Pydantic lanza 422 al no poder convertirlo a int.
# Ademas, el router se monta en main.py con prefix="/api/v1"
# (NO repetimos /usuarios aca — el tag del router ya lo agrupa).
# ═══════════════════════════════════════════════════════════════

@router.get("", response_model=UsuariosListResponse)
async def listar_usuarios(
    request: Request,
    q: Optional[str] = Query(None),
    rol: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    fuente: Optional[str] = Query(None, description="'ad' o 'local'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Lista usuarios de la BD con paginacion y filtros. ETO o ADMIN.
    (antes solo ADMIN, pero la UI de Parametrizacion la consume para ETOs)."""
    await require_eto_or_admin(request, db)

    # Query base
    base = select(Usuario).options(
        selectinload(Usuario.roles),
        selectinload(Usuario.modulos),
        selectinload(Usuario.area).selectinload(Area.gerencia),
        selectinload(Usuario.delegado),
    )

    # Filtros
    if q:
        pat = f"%{q.lower()}%"
        base = base.where(or_(
            func.lower(Usuario.username).like(pat),
            func.lower(Usuario.nombre_completo).like(pat),
            func.lower(Usuario.email).like(pat),
        ))
    if estado:
        try:
            estado_enum = EstadoUsuario(estado)
            base = base.where(Usuario.estado == estado_enum)
        except ValueError:
            pass
    if fuente == "ad":
        base = base.where(Usuario.azure_oid.isnot(None))
    elif fuente == "local":
        base = base.where(Usuario.azure_oid.is_(None))
    if rol:
        from app.models.usuario import usuario_roles
        base = base.join(usuario_roles, usuario_roles.c.usuario_id == Usuario.id).join(
            Rol, Rol.id == usuario_roles.c.rol_id
        ).where(Rol.codigo == rol)


    # Total + items
    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar_one()

    items_q = base.order_by(Usuario.nombre_completo.asc()).offset((page - 1) * page_size).limit(page_size)
    users = (await db.execute(items_q)).scalars().all()

    # KPIs (universo completo, no solo la pagina actual)
    total_all = (await db.execute(select(func.count()).select_from(Usuario))).scalar_one()
    activos_all = (await db.execute(
        select(func.count()).where(Usuario.estado == EstadoUsuario.ACTIVO)
    )).scalar_one()
    ausentes_all = (await db.execute(
        select(func.count()).where(Usuario.ausente == True)
    )).scalar_one()
    kpis = {
        "total": total_all,
        "activos": activos_all,
        "ausentes": ausentes_all,
    }

    return UsuariosListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_out(u) for u in users],
        kpis=kpis,
    )


@router.post("/sync-ad", response_model=SyncAdResponse)
async def sync_ad(
    request: Request,
    payload: SyncAdRequest = SyncAdRequest(),
    db: AsyncSession = Depends(get_db),
):
    """
    Sincroniza usuarios desde el AD real de COFAR a la BD local.
    Solo ADMIN.
    """
    await _require_admin(request, db)
    if not settings.ldap_enabled:
        raise HTTPException(
            status_code=503,
            detail="LDAP deshabilitado. Setea LDAP_ENABLED=true en .env y reinicia el backend."
        )

    t0 = datetime.utcnow()
    result = ad_service.ldap_search_users(query=None, page=1, page_size=payload.max_results)
    ad_users = result["items"]
    excluded_count = payload.max_results - len(ad_users)
    warnings = result.get("warnings", [])

    # Importar la helper de iniciales del auth.py
    from app.api.v1.auth import _calcular_iniciales

    def _truncar(s, max_len):
        """Truncar string a max_len chars, cuidando None."""
        if s is None:
            return None
        s = str(s).strip()
        if not s:
            return None
        if len(s) > max_len:
            logger.warning(f"Truncando campo de {len(s)} a {max_len} chars: {s[:60]}...")
            return s[:max_len]
        return s

    # Limites REALES del modelo Usuario (ver app/models/usuario.py).
    # Si el AD trae algo mas largo, se trunca a estos limites.
    LIMITS = {
        "username": 50,
        "azure_oid": 100,
        "email": 150,
        "nombre_completo": 200,
        "iniciales": 5,
        "cargo": 100,
        "ad_info": 2000,
        "ad_postal_code": 50,
    }

    creados = 0
    actualizados = 0
    sin_cambios = 0
    errores = 0
    excluidos_por_filtro = 0
    for ad_user in ad_users:
        try:
            sam = ad_user.get("sAMAccountName")
            if not sam:
                errores += 1
                continue

            # ─── Filtros adicionales (los de n8n) ───
            # 1) Saltar cuentas de equipo (terminan en $)
            if sam.endswith("$"):
                excluidos_por_filtro += 1
                continue
            # 2) Saltar cuentas con objectClass sin 'user' (equipos, grupos, etc.)
            oc = ad_user.get("objectClass")
            if oc:
                if isinstance(oc, list):
                    oc = " ".join(oc).lower()
                else:
                    oc = str(oc).lower()
                if "user" not in oc or "person" not in oc:
                    excluidos_por_filtro += 1
                    continue
            # 3) sAMAccountType: solo SAM_NORMAL_USER_ACCOUNT (805306368 = 0x30000000)
            sam_type = ad_user.get("sAMAccountType")
            if sam_type is not None:
                if isinstance(sam_type, list):
                    sam_type = sam_type[0] if sam_type else None
                if str(sam_type) != "805306368":
                    excluidos_por_filtro += 1
                    continue

            existing = (await db.execute(
                select(Usuario).where(Usuario.username == sam)
            )).scalar_one_or_none()

            # Truncar campos al limite REAL del modelo (varchar(N))
            nc = _truncar(ad_user.get("nombre_completo") or sam.title(), LIMITS["nombre_completo"])
            cargo = _truncar(ad_user.get("title") or "(sin cargo)", LIMITS["cargo"])
            email = _truncar(ad_user.get("mail") or f"{sam}@cofar.com", LIMITS["email"])
            ad_info = _truncar(ad_user.get("department"), LIMITS["ad_info"])
            # NO usamos azure_oid: el "sAMAccountName" (que guardamos en
            # username) es el identificador unico natural de AD. El campo
            # azure_oid en la BD queda None y se puede llenar despues si
            # se necesita mapear a Azure AD/Microsoft Graph.
            postal = _truncar(ad_user.get("postalCode"), LIMITS["ad_postal_code"])
            given = ad_user.get("givenName") or ""
            sn = ad_user.get("sn") or ""
            iniciales = _truncar(_calcular_iniciales(given, sn), LIMITS["iniciales"])
            sam_trunc = _truncar(sam, LIMITS["username"])

            if existing is None:
                user = Usuario(
                    username=sam_trunc,
                    email=email,
                    nombre_completo=nc or sam_trunc,
                    iniciales=iniciales or "?",
                    cargo=cargo or "(sin cargo)",
                    azure_oid=None,  # sAMAccountName es el ID unico
                    ad_info=ad_info,
                    ad_postal_code=postal,
                    ad_last_synced_at=datetime.utcnow(),
                    estado=EstadoUsuario.ACTIVO,
                    estado_delegacion=EstadoDelegacion.NA,
                )
                db.add(user)
                creados += 1
            else:
                changed = False
                if email and existing.email != email:
                    existing.email = email; changed = True
                if nc and existing.nombre_completo != nc:
                    existing.nombre_completo = nc; changed = True
                if cargo and existing.cargo != cargo:
                    existing.cargo = cargo; changed = True
                if iniciales and existing.iniciales != iniciales:
                    existing.iniciales = iniciales; changed = True
                if postal and existing.ad_postal_code != postal:
                    existing.ad_postal_code = postal; changed = True
                if ad_info and existing.ad_info != ad_info:
                    existing.ad_info = ad_info; changed = True
                if changed:
                    existing.ad_last_synced_at = datetime.utcnow()
                    actualizados += 1
                else:
                    sin_cambios += 1

            # Flush por usuario: si uno falla por longitud/unique/etc,
            # hace rollback SOLO de ese y sigue con el siguiente.
            # Asi no se cae toda la transaccion.
            try:
                await db.flush()
            except Exception as e_flush:
                await db.rollback()
                logger.warning(
                    f"Error insertando/actualizando {sam}: {str(e_flush)[:200]}. "
                    f"Continuando con el siguiente."
                )
                errores += 1
                # Restar el contador que ya se sumo (creados/actualizados)
                # El rollback ya revirtio el cambio en la sesion.
                if existing is None:
                    creados -= 1
                elif changed:
                    actualizados -= 1
                else:
                    sin_cambios -= 1
                continue
        except Exception as e:
            sam_log = ad_user.get("sAMAccountName", "?")
            logger.warning(f"Error procesando usuario AD {sam_log}: {e}")
            errores += 1
            await db.rollback()

    await db.commit()
    duracion = (datetime.utcnow() - t0).total_seconds()
    logger.info(
        f"Sync AD: {len(ad_users)} del AD, {creados} creados, {actualizados} actualizados, "
        f"{sin_cambios} sin cambios, {excluidos_por_filtro} excluidos por filtro, "
        f"{errores} errores, {duracion:.1f}s"
    )
    return SyncAdResponse(
        total_ad=len(ad_users),
        creados=creados,
        actualizados=actualizados,
        sin_cambios=sin_cambios,
        excluidos=excluded_count,
        errores=errores,
        duracion_seg=duracion,
        warnings=warnings,
    )


@router.get("/sync-status")
async def sync_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Estado del ultimo sync. ETO o ADMIN (sesion 22: cualquier
    usuario de parametrizacion debe poder ver el estado del sync)."""
    await require_eto_or_admin(request, db)
    last_sync = (await db.execute(
        select(Usuario.ad_last_synced_at)
        .where(Usuario.ad_last_synced_at.isnot(None))
        .order_by(Usuario.ad_last_synced_at.desc())
        .limit(1)
    )).scalar_one_or_none()

    total = (await db.execute(select(func.count()).select_from(Usuario))).scalar_one()
    ad_count = (await db.execute(
        select(func.count()).where(Usuario.azure_oid.isnot(None))
    )).scalar_one()
    local_count = total - ad_count

    return {
        "last_sync_at": last_sync.isoformat() if last_sync else None,
        "total_usuarios": total,
        "usuarios_del_ad": ad_count,
        "usuarios_locales": local_count,
    }


@router.get("/export")
async def export_usuarios(
    request: Request,
    formato: str = Query("xlsx", pattern="^(xlsx|csv)$", description="Formato: xlsx o csv"),
    q: Optional[str] = Query(None, description="Busca en username/nombre/email"),
    rol: Optional[str] = Query(None, description="Filtra por codigo de rol (ETO, ADMIN, etc.)"),
    estado: Optional[str] = Query(None, description="activo / inactivo / desvinculado / ausente"),
    area_id: Optional[int] = Query(None, ge=1),
    gerencia_id: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
):
    """
    Exporta la lista de usuarios a XLSX (default) o CSV.
    Genera un archivo con cabecera profesional (auto-width, freeze, filtros,
    totales, paleta pastel alineada con el design system del frontend).

    Si no se pasan filtros, exporta TODOS los usuarios.
    Solo ETO o ADMIN.
    """
    user_admin = await require_eto_or_admin(request, db)

    # Query base (mismos filtros que listar_usuarios)
    base = select(Usuario).options(
        selectinload(Usuario.roles),
        selectinload(Usuario.modulos),
        selectinload(Usuario.area).selectinload(Area.gerencia),
        selectinload(Usuario.delegado),
    )
    if q:
        pat = f"%{q.lower()}%"
        base = base.where(or_(
            func.lower(Usuario.username).like(pat),
            func.lower(Usuario.nombre_completo).like(pat),
            func.lower(Usuario.email).like(pat),
        ))
    if estado:
        try:
            estado_enum = EstadoUsuario(estado)
            base = base.where(Usuario.estado == estado_enum)
        except ValueError:
            pass
    if area_id is not None:
        base = base.where(Usuario.area_id == area_id)
    if gerencia_id is not None:
        # Join a traves del area
        base = base.join(Area, Area.id == Usuario.area_id).where(Area.gerencia_id == gerencia_id)
    if rol:
        from app.models.usuario import usuario_roles
        base = base.join(usuario_roles, usuario_roles.c.usuario_id == Usuario.id).join(
            Rol, Rol.id == usuario_roles.c.rol_id
        ).where(Rol.codigo == rol)

    users = (await db.execute(
        base.order_by(Usuario.nombre_completo.asc())
    )).scalars().all()

    # ─── Construir filas ───
    rows: list[list] = []
    for u in users:
        # Formato "Gerencia / Area" para que coincida con la UI
        # Prioridad: 1) area en BD, 2) ad_info (department del AD), 3) vacio
        gerencia_area = ""
        if u.area:
            partes = []
            if u.area.gerencia and u.area.gerencia.sigla:
                partes.append(u.area.gerencia.sigla)
            if u.area.sigla:
                partes.append(u.area.sigla)
            gerencia_area = " / ".join(partes)
        # Fallback al ad_info (department del AD) si no tiene area en BD
        if not gerencia_area and u.ad_info:
            # ad_info viene como "Tecnologia | Tercia SRL" del backend.
            # Para el export usamos el primer componente (gerencia aprox).
            gerencia_area = u.ad_info.split("|")[0].strip()
        # Delegado: nombre si existe, si no vacio
        delegado_nombre = u.delegado.nombre_completo if u.delegado else ""

        rows.append([
            u.id,
            u.username,
            u.nombre_completo,
            u.iniciales or "",
            u.email or "",
            u.cargo or "(sin cargo)",
            gerencia_area,  # "Gerencia / Area" (mismo formato que la UI, fallback ad_info)
            u.estado.value if hasattr(u.estado, "value") else str(u.estado),
            "SI" if u.ausente else "NO",
            (u.estado_delegacion.value if hasattr(u.estado_delegacion, "value") else str(u.estado_delegacion)),
            delegado_nombre,
            ", ".join(r.codigo for r in u.roles) or "(sin rol)",
            ", ".join(m.codigo for m in u.modulos) or "-",
            u.ad_postal_code or "",
            u.ad_last_synced_at.strftime("%Y-%m-%d %H:%M") if u.ad_last_synced_at else "",
        ])

    # ─── KPIs (totales) ───
    total = len(rows)
    activos = sum(1 for r in rows if r[7] == "activo")
    ausentes = sum(1 for r in rows if r[8] == "SI")
    inactivos = sum(1 for r in rows if r[7] in ("inactivo", "desvinculado"))

    total_row = [
        "TOTAL", f"{total} usuarios", "", "", "", "", "",
        f"{activos} activos", f"{ausentes} ausentes", f"{inactivos} inactivos",
        "", "", "", "", "",
    ]

    headers = [
        "ID", "Username", "Nombre Completo", "Inic.", "Email", "Cargo",
        "Gerencia / Area",  # unificado: formato "GNS / AREA"
        "Estado", "Ausente",
        "Delegacion", "Delegado", "Roles", "Modulos", "Cód. SAP", "Ultimo Sync AD",
    ]

    # Alinear: ID y fechas centrados/right, resto izquierda
    column_alignments = {1: "center", 4: "center", 8: "center", 9: "center", 10: "center", 14: "center"}

    if formato == "xlsx":
        file_bytes = build_excel(
            headers=headers,
            rows=rows,
            sheet_name="Usuarios SGD",
            title=f"Listado de Usuarios — COFAR SGD (generado por {user_admin.username})",
            total_row=total_row,
            column_alignments=column_alignments,
        )
        filename = f"usuarios_sgd_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        await write_audit(
            db, request, user_admin,
            accion="EXPORT", recurso="usuario", recurso_id=None,
            descripcion=f"Export de {total} usuarios a XLSX",
            detalles={"formato": "xlsx", "total": total, "filtros": {"q": q, "rol": rol, "estado": estado, "area_id": area_id, "gerencia_id": gerencia_id}},
        )
        await db.commit()
        return Response(
            content=file_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # CSV
    file_bytes = build_csv(headers=headers, rows=rows, total_row=total_row)
    filename = f"usuarios_sgd_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    await write_audit(
        db, request, user_admin,
        accion="EXPORT", recurso="usuario", recurso_id=None,
        descripcion=f"Export de {total} usuarios a CSV",
        detalles={"formato": "csv", "total": total, "filtros": {"q": q, "rol": rol, "estado": estado, "area_id": area_id, "gerencia_id": gerencia_id}},
    )
    await db.commit()
    return Response(
        content=file_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── /{user_id} generico DEBE ir AL FINAL (captura cualquier string) ───

@router.get("/{user_id}", response_model=UsuarioOut)
async def get_usuario(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Detalle de un usuario por id. ETO o ADMIN."""
    await require_eto_or_admin(request, db)
    user = (await db.execute(
        select(Usuario).where(Usuario.id == user_id)
        .options(
            selectinload(Usuario.roles),
            selectinload(Usuario.modulos),
            selectinload(Usuario.area).selectinload(Area.gerencia),
            selectinload(Usuario.delegado),
        )
    )).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado")
    return _to_out(user)


# ─── Sesion B - tarea #9e: override vacaciones ───

@router.patch("/{user_id}", response_model=UsuarioOut)
async def update_usuario_override(
    user_id: int,
    payload: UsuarioUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Override administrativo de un usuario (US-9.05).
    Solo ETO o ADMIN. Audita TODOS los cambios con detalle antes/despues.

    Casos tipicos:
      - Marcar vacaciones: {ausente: true, observaciones: "Vacaciones 15-30 jul"}
      - Suspender: {estado: "inactivo", observaciones: "Suspendido por X"}
      - Reactivar: {estado: "activo", ausente: false}
    """
    user_admin = await require_eto_or_admin(request, db)

    target = (await db.execute(
        select(Usuario).where(Usuario.id == user_id)
        .options(
            selectinload(Usuario.roles),
            selectinload(Usuario.modulos),
            selectinload(Usuario.area).selectinload(Area.gerencia),
            selectinload(Usuario.delegado),
        )
    )).scalar_one_or_none()
    if target is None:
        raise HTTPException(404, f"Usuario {user_id} no encontrado")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return _to_out(target)

    observaciones = data.pop("observaciones", None)
    rol_codigo = data.pop("rol_codigo", None)
    delegado_id = data.pop("delegado_id", None)

    antes = {
        "estado": target.estado.value if hasattr(target.estado, "value") else str(target.estado),
        "ausente": target.ausente,
        "estado_delegacion": target.estado_delegacion.value if hasattr(target.estado_delegacion, "value") else str(target.estado_delegacion),
        "roles": [r.codigo for r in target.roles],
        "delegado_id": target.delegado_id,
    }

    if "estado" in data and data["estado"] is not None:
        target.estado = data["estado"]
    if "ausente" in data and data["ausente"] is not None:
        target.ausente = data["ausente"]
    if "estado_delegacion" in data and data["estado_delegacion"] is not None:
        target.estado_delegacion = data["estado_delegacion"]

    # ─── Asignar/cambiar rol ───
    # Si se mando rol_codigo, se reemplazan TODOS los roles del usuario por ese.
    if rol_codigo is not None:
        from app.models.usuario import usuario_roles
        # Buscar el rol por codigo
        rol_obj = (await db.execute(
            select(Rol).where(Rol.codigo == rol_codigo)
        )).scalar_one_or_none()
        if rol_obj is None:
            raise HTTPException(404, f"Rol '{rol_codigo}' no existe")
        # Limpiar roles anteriores
        await db.execute(
            usuario_roles.delete().where(usuario_roles.c.usuario_id == target.id)
        )
        # Asignar el nuevo
        await db.execute(
            usuario_roles.insert().values(usuario_id=target.id, rol_id=rol_obj.id)
        )
        logger.info(f"Usuario {target.username}: rol -> {rol_codigo}")

    # ─── Asignar/quitar delegado ───
    # Si se mando delegado_id (puede ser None explicito para quitar, o un int para asignar)
    if "delegado_id" in payload.model_fields_set or delegado_id is not None:
        if delegado_id is not None and delegado_id == target.id:
            raise HTTPException(400, "Un usuario no puede ser su propio delegado")
        if delegado_id is not None:
            # Validar que el delegado existe y esta activo
            delegado_user = (await db.execute(
                select(Usuario).where(Usuario.id == delegado_id)
            )).scalar_one_or_none()
            if delegado_user is None:
                raise HTTPException(404, f"Usuario delegado {delegado_id} no existe")
            if delegado_user.estado == EstadoUsuario.DESVINCULADO:
                raise HTTPException(400, f"El usuario delegado {delegado_id} esta desvinculado")
        target.delegado_id = delegado_id
        # Si se asigna un delegado, marcar estado_delegacion=asignado;
        # si se quita, depende de si requiere_delegado (lo decide el caller).
        if delegado_id is not None:
            target.estado_delegacion = EstadoDelegacion.ASIGNADO
        logger.info(
            f"Usuario {target.username}: delegado_id -> {delegado_id} "
            f"(estado_delegacion={target.estado_delegacion.value})"
        )

    await db.commit()
    # Expirar explicitamente para forzar reload de relaciones (especialmente
    # `roles` que fue modificada por delete+insert en la tabla asociacion).
    db.expire(target)
    target = (await db.execute(
        select(Usuario).where(Usuario.id == user_id)
        .options(
            selectinload(Usuario.roles),
            selectinload(Usuario.modulos),
            selectinload(Usuario.area).selectinload(Area.gerencia),
            selectinload(Usuario.delegado),
        )
    )).scalar_one()

    despues = {
        "estado": target.estado.value if hasattr(target.estado, "value") else str(target.estado),
        "ausente": target.ausente,
        "estado_delegacion": target.estado_delegacion.value if hasattr(target.estado_delegacion, "value") else str(target.estado_delegacion),
        "roles": [r.codigo for r in target.roles],
        "delegado_id": target.delegado_id,
    }

    await write_audit(
        db, request, user_admin,
        accion="OVERRIDE", recurso="usuario", recurso_id=target.id,
        descripcion=f"Override administrativo sobre {target.username} (campos: {list(data.keys())})",
        detalles={"antes": antes, "despues": despues, "campos": list(data.keys()), "observaciones": observaciones},
    )
    await db.commit()
    logger.info(
        f"Override de usuario {target.username} (id={target.id}) "
        f"por {user_admin.username} (campos={list(data.keys())})"
    )
    return _to_out(target)
