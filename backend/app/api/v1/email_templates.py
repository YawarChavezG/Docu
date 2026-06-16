"""
api/v1/email_templates.py — CRUD de plantillas de notificacion (US-9.04).

Catalogo cerrado de 6 plantillas (5 del .docx + 1 del PDF).
La UI no crea plantillas nuevas, solo edita las 6 existentes.

Endpoints (todos bajo prefix /api/v1/email-templates):
  GET    /                          lista las 6 plantillas
  GET    /{codigo}                  detalle (codigo = "NUEVA_TAREA" etc)
  PATCH  /{codigo}                  update de asunto/cuerpo/variables/activo
  POST   /{codigo}/preview          renderiza con vars de prueba (Boton "Previsualizar")

GETs no requieren auth (la UI los carga al iniciar Parametrizacion > Plantillas).
Mutaciones requieren ETO o ADMIN.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jinja2 import Environment, StrictUndefined, TemplateError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_eto_or_admin
from app.models.email_template import EmailTemplate, CodigoPlantilla
from app.schemas.email_template import (
    EmailTemplateListResponse,
    EmailTemplateOut,
    EmailTemplatePreviewRequest,
    EmailTemplatePreviewResponse,
    EmailTemplateUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email-templates", tags=["Email Templates"])

# Jinja2 con StrictUndefined: si una var no esta en el dict, lanza error
# (asi el preview muestra cuales vars faltan en vez de renderizar vacio).
_jinja = Environment(undefined=StrictUndefined, autoescape=True)


# ─── Helpers ───

def _parse_codigo(codigo: str) -> CodigoPlantilla:
    """Convierte string a enum. 404 si no es valido."""
    try:
        return CodigoPlantilla(codigo)
    except ValueError:
        valid = ", ".join(c.value for c in CodigoPlantilla)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Codigo de plantilla '{codigo}' no existe. Validos: {valid}",
        )


async def _get_by_codigo(db: AsyncSession, codigo: CodigoPlantilla) -> EmailTemplate:
    t = (await db.execute(
        select(EmailTemplate).where(EmailTemplate.codigo == codigo)
    )).scalar_one_or_none()
    if t is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plantilla '{codigo.value}' no existe (ejecutar seed_email_templates.py)",
        )
    return t


def _render(template_str: str, vars_dict: dict) -> tuple[str, list[str]]:
    """
    Renderiza un template Jinja2 con StrictUndefined.
    Devuelve (rendered, vars_faltantes).
    Las vars no provistas en el dict se reportan como faltantes (NO fallan).
    """
    missing: list[str] = []
    try:
        tpl = _jinja.from_string(template_str)
    except TemplateError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template invalido: {e}",
        )

    class _LenientOnes(StrictUndefined):
        def __str__(self):
            missing.append(self._undefined_name)
            return ""

    env = Environment(undefined=_LenientOnes, autoescape=True)
    try:
        rendered = env.from_string(template_str).render(**vars_dict)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error renderizando template: {e}",
        )
    return rendered, list(set(missing))


# ─── Endpoints ───

@router.get("", response_model=EmailTemplateListResponse)
async def list_email_templates(
    db: AsyncSession = Depends(get_db),
):
    """Lista las 6 plantillas. No requiere auth (UI las carga al iniciar)."""
    rows = (await db.execute(
        select(EmailTemplate).order_by(EmailTemplate.codigo)
    )).scalars().all()
    return EmailTemplateListResponse(
        total=len(rows),
        items=[EmailTemplateOut.model_validate(r) for r in rows],
    )


@router.get("/{codigo}", response_model=EmailTemplateOut)
async def get_email_template(
    codigo: str,
    db: AsyncSession = Depends(get_db),
):
    """Detalle. No requiere auth."""
    enum_val = _parse_codigo(codigo)
    t = await _get_by_codigo(db, enum_val)
    return EmailTemplateOut.model_validate(t)


@router.patch("/{codigo}", response_model=EmailTemplateOut)
async def update_email_template(
    codigo: str,
    payload: EmailTemplateUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Edita una plantilla (asunto, cuerpo, variables, activo). Requiere ETO o ADMIN.
    NO se puede cambiar el codigo (es PK logica del catalogo cerrado).
    """
    await require_eto_or_admin(request, db)
    enum_val = _parse_codigo(codigo)
    t = await _get_by_codigo(db, enum_val)

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return EmailTemplateOut.model_validate(t)

    for field, value in data.items():
        setattr(t, field, value)

    await db.commit()
    await db.refresh(t)
    logger.info(f"Plantilla editada: {t.codigo.value} (campos={list(data.keys())})")
    return EmailTemplateOut.model_validate(t)


@router.post("/{codigo}/preview", response_model=EmailTemplatePreviewResponse)
async def preview_email_template(
    codigo: str,
    payload: EmailTemplatePreviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Renderiza la plantilla con vars de prueba (Boton "Previsualizar" del US-9.04).
    Devuelve asunto y cuerpo renderizados + lista de vars faltantes.
    No modifica la BD.

    No requiere auth (preview es idempotente y solo renderiza).
    """
    enum_val = _parse_codigo(codigo)
    t = await _get_by_codigo(db, enum_val)

    asunto, missing_a = _render(t.asunto, payload.vars)
    cuerpo, missing_c = _render(t.cuerpo_html, payload.vars)
    missing = list(set(missing_a + missing_c))

    return EmailTemplatePreviewResponse(
        codigo=enum_val,
        asunto_rendered=asunto,
        cuerpo_html_rendered=cuerpo,
        vars_aplicadas=payload.vars,
        vars_faltantes=missing,
    )
