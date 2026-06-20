"""
seed_email_templates.py — COFAR SGD (Sesion A, tarea #7)

Sembra las 6 plantillas de notificacion por email (US-9.04):
  5 del PLANTILLAS DE NOTIFICACION.docx
  1 del PDF HISTORIAS DE USUARIO (auto-delegacion-activada, contenido stub)

Uso: docker exec sgd-backend python scripts/seed_email_templates.py
Idempotente: si la plantilla existe, actualiza asunto/cuerpo/variables.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.email_template import EmailTemplate, CodigoPlantilla


# Variables disponibles en TODAS las plantillas (panel UI "Etiquetas Disponibles")
# US-9.04 del PDF oficial
VARS_DISPONIBLES = [
    "{{CODIGO}}", "{{TITULO}}", "{{USUARIO}}", "{{FECHA_LIMITE}}",
    "{{ETAPA}}", "{{LINK}}", "{{GERENCIA}}", "{{OBSERVACION}}",
]


PLANTILLAS = [
    {
        "codigo": CodigoPlantilla.NUEVA_TAREA,
        "nombre": "Nueva Tarea Asignada",
        "asunto": "[COFAR - SGD] Nueva tarea asignada: [{{CODIGO}}] - [{{TITULO}}]",
        "cuerpo_html": """\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #1a5fb4;">Nueva Tarea Asignada</h2>
  <p>Estimado/a <strong>{{USUARIO}}</strong>,</p>
  <p>Se le ha asignado una nueva tarea en el Sistema de Gestion Documental:</p>
  <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Codigo</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{CODIGO}}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Titulo</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{TITULO}}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Gerencia</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{GERENCIA}}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Etapa</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{ETAPA}}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Fecha limite</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{FECHA_LIMITE}}</td></tr>
  </table>
  <p>Para acceder al documento haga clic en el siguiente enlace:</p>
  <p><a href="{{LINK}}" style="background:#1a5fb4;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;">Ver documento</a></p>
  <hr style="margin-top: 30px;">
  <p style="color: #888; font-size: 11px;">Este correo fue generado automaticamente por el SGD COFAR. No responda a este mensaje.</p>
</div>
""",
        "variables_json": VARS_DISPONIBLES,
    },
    {
        "codigo": CodigoPlantilla.ALERTA_VENCIMIENTO,
        "nombre": "Alerta de Vencimiento",
        "asunto": "[COFAR - SGD] URGENTE: Tarea proxima a vencer [{{CODIGO}}]",
        "cuerpo_html": """\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #d97706;">Alerta de Vencimiento</h2>
  <p>Estimado/a <strong>{{USUARIO}}</strong>,</p>
  <p>La siguiente tarea esta proxima a vencer:</p>
  <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Codigo</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{CODIGO}}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Titulo</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{TITULO}}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Etapa</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{ETAPA}}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Fecha limite</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd; color: #d97706; font-weight: bold;">{{FECHA_LIMITE}}</td></tr>
  </table>
  <p>Por favor complete la tarea a la brevedad posible.</p>
  <p><a href="{{LINK}}">Acceder al documento</a></p>
</div>
""",
        "variables_json": VARS_DISPONIBLES,
    },
    {
        "codigo": CodigoPlantilla.DOCUMENTO_APROBADO,
        "nombre": "Documento Aprobado",
        "asunto": "[COFAR - SGD] Documento aprobado: [{{CODIGO}}] - [{{TITULO}}]",
        "cuerpo_html": """\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #059669;">Documento Aprobado</h2>
  <p>Estimado/a <strong>{{USUARIO}}</strong>,</p>
  <p>El siguiente documento ha sido <strong>aprobado</strong> y se publica en la Lista Maestra:</p>
  <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Codigo</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{CODIGO}}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Titulo</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{TITULO}}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Gerencia</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{GERENCIA}}</td></tr>
  </table>
  <p>Ya esta disponible para descarga desde la Lista Maestra del SGD.</p>
  <p><a href="{{LINK}}">Ver en Lista Maestra</a></p>
</div>
""",
        "variables_json": VARS_DISPONIBLES,
    },
    {
        "codigo": CodigoPlantilla.DOCUMENTO_OBSERVADO,
        "nombre": "Documento Observado",
        "asunto": "[COFAR - SGD] Documento observado: [{{CODIGO}}] - [{{TITULO}}]",
        "cuerpo_html": """\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #dc2626;">Documento Observado</h2>
  <p>Estimado/a <strong>{{USUARIO}}</strong>,</p>
  <p>El siguiente documento ha sido <strong>observado</strong> y requiere correcciones:</p>
  <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Codigo</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{CODIGO}}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Titulo</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{TITULO}}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Etapa</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{ETAPA}}</td></tr>
  </table>
  <p><strong>Observacion del revisor:</strong></p>
  <blockquote style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 12px; margin: 12px 0;">
    {{OBSERVACION}}
  </blockquote>
  <p>Por favor ingrese al SGD para revisar las observaciones y realizar las correcciones.</p>
  <p><a href="{{LINK}}">Ir al documento</a></p>
</div>
""",
        "variables_json": VARS_DISPONIBLES,
    },
    {
        "codigo": CodigoPlantilla.EVALUACION_PENDIENTE,
        "nombre": "Evaluacion Pendiente",
        "asunto": "[COFAR - SGD] Evaluacion pendiente: [{{TITULO}}]",
        "cuerpo_html": """\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #1a5fb4;">Evaluacion Pendiente</h2>
  <p>Estimado/a <strong>{{USUARIO}}</strong>,</p>
  <p>Tiene una evaluacion de capacitacion pendiente:</p>
  <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Documento</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{CODIGO}} - {{TITULO}}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Fecha limite</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{FECHA_LIMITE}}</td></tr>
  </table>
  <p>Complete la evaluacion antes de la fecha limite.</p>
  <p><a href="{{LINK}}">Tomar evaluacion</a></p>
</div>
""",
        "variables_json": VARS_DISPONIBLES,
    },
    {
        "codigo": CodigoPlantilla.AUTO_DELEGACION_ACTIVADA,
        "nombre": "Auto-delegacion Activada",
        "asunto": "[COFAR - SGD] Auto-delegacion activada en [{{CODIGO}}]",
        # Plantilla 6 del PDF oficial (no estaba en el .docx). Contenido stub
        # coherente con el flujo: si pasaron N dias sin accion, el sistema
        # delega automaticamente al jefe inmediato.
        "cuerpo_html": """\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #d97706;">Auto-delegacion Activada</h2>
  <p>Estimado/a <strong>{{USUARIO}}</strong>,</p>
  <p>Por haber transcurrido <strong>{{ETAPA}}</strong> dias habiles sin accion sobre la siguiente tarea, el SGD ha activado la auto-delegacion:</p>
  <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Codigo</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{CODIGO}}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Titulo</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{TITULO}}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Gerencia</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{GERENCIA}}</td></tr>
  </table>
  <p>La tarea ha sido reasignada automaticamente. Si necesita recuperarla, contacte al ETO.</p>
  <p><a href="{{LINK}}">Ver historial</a></p>
</div>
""",
        "variables_json": VARS_DISPONIBLES,
    },
]


async def seed_templates(db: AsyncSession) -> tuple[int, int]:
    creados = 0
    actualizados = 0
    for data in PLANTILLAS:
        existing = (await db.execute(
            select(EmailTemplate).where(EmailTemplate.codigo == data["codigo"])
        )).scalar_one_or_none()

        if existing is None:
            t = EmailTemplate(**data, activo=True)
            db.add(t)
            print(f"  [+] {data['codigo'].value} - {data['nombre']!r}")
            creados += 1
        else:
            changed = False
            for field in ("nombre", "asunto", "cuerpo_html", "variables_json"):
                new_val = data[field]
                if getattr(existing, field) != new_val:
                    setattr(existing, field, new_val)
                    changed = True
            if not existing.activo:
                existing.activo = True
                changed = True
            if changed:
                print(f"  [~] {data['codigo'].value} actualizado")
                actualizados += 1
            else:
                print(f"  [=] {data['codigo'].value} sin cambios")
        await db.flush()
    return creados, actualizados


async def main() -> None:
    print("=" * 70)
    print("COFAR SGD - Seed Email Templates (US-9.04)")
    print("=" * 70)
    print(f"Total: {len(PLANTILLAS)} plantillas (5 del .docx + 1 del PDF)")

    async with AsyncSessionLocal() as db:
        try:
            creados, actualizados = await seed_templates(db)
            await db.commit()
            print("\n" + "=" * 70)
            print(f"Resultado: {creados} creadas, {actualizados} actualizadas, "
                  f"{len(PLANTILLAS) - creados - actualizados} sin cambios")
            print("=" * 70)
        except Exception as e:
            await db.rollback()
            print(f"\nError durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
