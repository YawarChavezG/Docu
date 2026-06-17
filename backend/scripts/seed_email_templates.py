"""
seed_email_templates.py — COFAR SGD (Sesion 13: 10 plantillas)

Sembra las 10 plantillas de notificacion por email (US-9.04):
  10 de docs/PR/PLANTILLAS DE NOTIFICACION.md
  + 1 del PDF HISTORIAS DE USUARIO (auto-delegacion)

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
VARS_COMUNES = [
    "{{CODIGO}}", "{{TITULO}}", "{{USUARIO}}", "{{FECHA_LIMITE}}",
    "{{ETAPA}}", "{{LINK}}", "{{GERENCIA}}", "{{OBSERVACION}}",
    "{{REASIGNADO_POR}}", "{{TAREA}}", "{{FECHA_VENCIMIENTO}}",
]

PLANTILLAS = [
    # ─── 1. Asignación de Revisión ───
    {
        "codigo": CodigoPlantilla.ASIG_REVISION,
        "nombre": "Asignación de Revisión",
        "asunto": "[COFAR SGD] REVISAR DOCUMENTO - {{CODIGO}}",
        "cuerpo_html": """\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #1a5fb4;">REVISAR DOCUMENTO</h2>
  <p>Estimado colaborador, le notificamos que se le ha asignado una tarea de <strong>REVISIÓN</strong> en el Sistema de Gestión Documental:</p>
  <p><strong>Código:</strong> {{CODIGO}}<br>
  <strong>Título:</strong> {{TITULO}}</p>
  <p>Para realizar la revisión correspondiente, favor ingresar al siguiente enlace: {{LINK}}</p>
  <p>Agradecemos realizar la actividad dentro del plazo establecido.</p>
  <p>Si tiene alguna duda, favor comunicarse con el área de ETO.<br>Gracias.</p>
  <hr><p style="color: #888; font-size: 11px;">Este correo fue generado automáticamente por el SGD COFAR.</p>
</div>""",
        "variables_json": VARS_COMUNES,
    },
    # ─── 2. Asignación de Aprobación ───
    {
        "codigo": CodigoPlantilla.ASIG_APROBACION,
        "nombre": "Asignación de Aprobación",
        "asunto": "[COFAR SGD] APROBAR DOCUMENTO - {{CODIGO}}",
        "cuerpo_html": """\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #1a5fb4;">APROBAR DOCUMENTO</h2>
  <p>Estimado colaborador, le notificamos que se le ha asignado una tarea de <strong>APROBACIÓN</strong> en el Sistema de Gestión Documental:</p>
  <p><strong>Código:</strong> {{CODIGO}}<br>
  <strong>Título:</strong> {{TITULO}}</p>
  <p>Para revisar y aprobar el documento, favor ingresar al siguiente enlace: {{LINK}}</p>
  <p>Agradecemos realizar la actividad dentro del plazo establecido.</p>
  <p>Si tiene alguna duda, favor comunicarse con el área de ETO.<br>Gracias.</p>
  <hr><p style="color: #888; font-size: 11px;">Este correo fue generado automáticamente por el SGD COFAR.</p>
</div>""",
        "variables_json": VARS_COMUNES,
    },
    # ─── 3. Solicitud de Corrección ───
    {
        "codigo": CodigoPlantilla.SOLICITUD_CORRECCION,
        "nombre": "Solicitud de Corrección",
        "asunto": "[COFAR SGD] CORREGIR DOCUMENTO - {{CODIGO}}",
        "cuerpo_html": """\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #d97706;">CORREGIR DOCUMENTO</h2>
  <p>Estimado colaborador, le notificamos que el siguiente documento requiere la realización de <strong>CORRECCIONES</strong>:</p>
  <p><strong>Código:</strong> {{CODIGO}}<br>
  <strong>Título:</strong> {{TITULO}}</p>
  <p>Favor ingresar al siguiente enlace para revisar las observaciones registradas y efectuar las correcciones correspondientes: {{LINK}}</p>
  <p>Agradecemos atender la solicitud dentro del plazo establecido.</p>
  <p>Si tiene alguna duda, favor comunicarse con el área de ETO.<br>Gracias.</p>
  <hr><p style="color: #888; font-size: 11px;">Este correo fue generado automáticamente por el SGD COFAR.</p>
</div>""",
        "variables_json": VARS_COMUNES,
    },
    # ─── 4. Control de Lectura Asignado ───
    {
        "codigo": CodigoPlantilla.CONTROL_LECTURA,
        "nombre": "Control de Lectura Asignado",
        "asunto": "[COFAR SGD] REGISTRAR CONTROL DE LECTURA - {{CODIGO}}",
        "cuerpo_html": """\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #1a5fb4;">REGISTRAR CONTROL DE LECTURA</h2>
  <p>Estimado colaborador, le notificamos que debe realizar el <strong>CONTROL DE LECTURA</strong> en el Sistema de Gestión Documental correspondiente al siguiente documento:</p>
  <p><strong>Código:</strong> {{CODIGO}}<br>
  <strong>Título:</strong> {{TITULO}}<br>
  <strong>Versión:</strong> 00</p>
  <p>Para realizar la lectura y confirmación correspondiente, favor ingresar al siguiente enlace: {{LINK}}</p>
  <p>Su participación es importante para asegurar la difusión y conocimiento de la documentación vigente.</p>
  <p>Si tiene alguna duda, favor comunicarse con el área de ETO.<br>Gracias.</p>
  <hr><p style="color: #888; font-size: 11px;">Este correo fue generado automáticamente por el SGD COFAR.</p>
</div>""",
        "variables_json": VARS_COMUNES,
    },
    # ─── 5. Evaluación Asignada ───
    {
        "codigo": CodigoPlantilla.EVALUACION_ASIGNADA,
        "nombre": "Evaluación Asignada",
        "asunto": "[COFAR SGD] REGISTRAR EVALUACION DOCUMENTAL - {{CODIGO}}",
        "cuerpo_html": """\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #1a5fb4;">REGISTRAR EVALUACIÓN DOCUMENTAL</h2>
  <p>Estimado colaborador, le notificamos que debe realizar una <strong>EVALUACIÓN</strong> en el Sistema de Gestión Documental correspondiente al siguiente documento:</p>
  <p><strong>Código:</strong> {{CODIGO}}<br>
  <strong>Título:</strong> {{TITULO}}<br>
  <strong>Versión:</strong> 00</p>
  <p>Para realizar la evaluación correspondiente, favor ingresar al siguiente enlace: {{LINK}}</p>
  <p>Agradecemos completar la actividad dentro del plazo establecido.</p>
  <p>Si tiene alguna duda, favor comunicarse con el área de ETO.<br>Gracias.</p>
  <hr><p style="color: #888; font-size: 11px;">Este correo fue generado automáticamente por el SGD COFAR.</p>
</div>""",
        "variables_json": VARS_COMUNES,
    },
    # ─── 6. Liberación de Documento ───
    {
        "codigo": CodigoPlantilla.LIBERACION_DOCUMENTO,
        "nombre": "Liberación de Documento",
        "asunto": "[COFAR SGD] LIBERAR DOCUMENTO - {{CODIGO}}",
        "cuerpo_html": """\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #1a5fb4;">LIBERAR DOCUMENTO</h2>
  <p>Estimado colaborador, le notificamos que el siguiente documento se encuentra listo para su <strong>LIBERACIÓN</strong>:</p>
  <p><strong>Código:</strong> {{CODIGO}}<br>
  <strong>Título:</strong> {{TITULO}}</p>
  <p>Para realizar la liberación correspondiente, favor ingresar al siguiente enlace: {{LINK}}</p>
  <p>Gracias.</p>
  <hr><p style="color: #888; font-size: 11px;">Este correo fue generado automáticamente por el SGD COFAR.</p>
</div>""",
        "variables_json": VARS_COMUNES,
    },
    # ─── 7. Documento Aprobado ───
    {
        "codigo": CodigoPlantilla.DOCUMENTO_APROBADO,
        "nombre": "Documento Aprobado (Difusión)",
        "asunto": "[COFAR SGD] DIFUSION DOCUMENTAL ({{CODIGO}} v{{VERSION}})",
        "cuerpo_html": """\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #059669;">DIFUSIÓN DOCUMENTAL</h2>
  <p>Estimado colaborador, le informamos que el siguiente documento ha sido <strong>APROBADO</strong> y se encuentra vigente a partir de la fecha:</p>
  <p><strong>Código:</strong> {{CODIGO}}<br>
  <strong>Título:</strong> {{TITULO}}<br>
  <strong>Versión:</strong> 00</p>
  <p>Los documentos y sus formularios se encuentran disponibles para lectura y uso en el siguiente enlace: {{LINK}}</p>
  <p><strong>CONSIDERACIONES ESPECIALES:</strong></p>
  <ul>
    <li>Difundir el documento a sus equipos de trabajo</li>
    <li>Asegurarse de no contar con documentos físicos en versiones anteriores a la mencionada, de ser así favor remitir dichas copias al área de ETO.</li>
    <li>A partir de la fecha deben utilizarse los registros actualizados en las versiones correspondientes.</li>
    <li>Si las áreas involucradas requieren una copia controlada física favor comunicarse con el área de ETO</li>
  </ul>
  <p>Gracias.</p>
  <hr><p style="color: #888; font-size: 11px;">Este correo fue generado automáticamente por el SGD COFAR.</p>
</div>""",
        "variables_json": VARS_COMUNES,
    },
    # ─── 8. Reasignación por Incumplimiento ───
    {
        "codigo": CodigoPlantilla.REASIG_INCUMPLIMIENTO,
        "nombre": "Reasignación por Incumplimiento",
        "asunto": "[COFAR SGD] REASIGNACION DE TAREA - {{CODIGO}}",
        "cuerpo_html": """\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #dc2626;">REASIGNACIÓN DE TAREA</h2>
  <p>Estimado colaborador, le notificamos que la siguiente tarea ha sido <strong>REASIGNADA</strong> debido al incumplimiento del plazo establecido para ejecutar la tarea:</p>
  <p><strong>Código:</strong> {{CODIGO}}<br>
  <strong>Título:</strong> {{TITULO}}<br>
  <strong>Tarea:</strong> {{TAREA}}</p>
  <p><strong>Nuevo usuario asignado:</strong> {{USUARIO}}</p>
  <p>Si tiene alguna duda, favor comunicarse con el área de ETO.<br>Gracias.</p>
  <hr><p style="color: #888; font-size: 11px;">Este correo fue generado automáticamente por el SGD COFAR.</p>
</div>""",
        "variables_json": VARS_COMUNES,
    },
    # ─── 9. Reasignación Manual ───
    {
        "codigo": CodigoPlantilla.REASIG_MANUAL,
        "nombre": "Reasignación Manual",
        "asunto": "[COFAR SGD] REASIGNACION DE TAREA - {{CODIGO}}",
        "cuerpo_html": """\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #1a5fb4;">REASIGNACIÓN DE TAREA</h2>
  <p>Estimado colaborador, le notificamos que se le ha reasignado una tarea de <strong>REVISIÓN / APROBACIÓN</strong> en el Sistema de Gestión Documental:</p>
  <p><strong>Código:</strong> {{CODIGO}}<br>
  <strong>Título:</strong> {{TITULO}}</p>
  <p><strong>Usuario que ha reasignado la tarea:</strong> {{REASIGNADO_POR}}</p>
  <p>Para revisar y aprobar el documento, favor ingresar al siguiente enlace: {{LINK}}</p>
  <p>Agradecemos realizar la actividad dentro del plazo establecido.</p>
  <p>Si tiene alguna duda, favor comunicarse con el área de ETO.<br>Gracias.</p>
  <hr><p style="color: #888; font-size: 11px;">Este correo fue generado automáticamente por el SGD COFAR.</p>
</div>""",
        "variables_json": VARS_COMUNES,
    },
    # ─── 10. Tarea Próxima a Vencer ───
    {
        "codigo": CodigoPlantilla.TAREA_PROXIMA_VENCER,
        "nombre": "Tarea Próxima a Vencer",
        "asunto": "[COFAR SGD] TAREA PRÓXIMA A VENCER - {{CODIGO}}",
        "cuerpo_html": """\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #dc2626;">⚠️ TAREA PRÓXIMA A VENCER</h2>
  <p>Estimado colaborador, le recordamos que tiene una tarea próxima a vencer en el Sistema de Gestión Documental:</p>
  <p><strong>Código:</strong> {{CODIGO}}<br>
  <strong>Título:</strong> {{TITULO}}<br>
  <strong>Tarea:</strong> {{TAREA}}<br>
  <strong>Fecha límite:</strong> {{FECHA_VENCIMIENTO}}</p>
  <p>Favor ingresar al siguiente enlace para completar la actividad pendiente: {{LINK}}</p>
  <p>Gracias.</p>
  <p style="color: #888; font-size: 10px;"><em>Nota: esta notificación se envía cada día desde que la tarea se semáforo en ROJO hasta su ejecución.</em></p>
  <hr><p style="color: #888; font-size: 11px;">Este correo fue generado automáticamente por el SGD COFAR.</p>
</div>""",
        "variables_json": VARS_COMUNES,
    },
    # ─── 11. Auto-delegación (mantenida del PDF original) ───
    {
        "codigo": CodigoPlantilla.AUTO_DELEGACION_ACTIVADA,
        "nombre": "Auto-delegación Activada",
        "asunto": "[COFAR SGD] Auto-delegación activada en {{CODIGO}}",
        "cuerpo_html": """\
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #d97706;">Auto-delegación Activada</h2>
  <p>Estimado/a <strong>{{USUARIO}}</strong>,</p>
  <p>Por haber transcurrido <strong>{{ETAPA}}</strong> días hábiles sin acción sobre la siguiente tarea, el SGD ha activado la auto-delegación:</p>
  <p><strong>Código:</strong> {{CODIGO}}<br>
  <strong>Título:</strong> {{TITULO}}<br>
  <strong>Gerencia:</strong> {{GERENCIA}}</p>
  <p>La tarea ha sido reasignada automáticamente. Si necesita recuperarla, contacte al ETO.</p>
  <p><a href="{{LINK}}">Ver historial</a></p>
  <hr><p style="color: #888; font-size: 11px;">Este correo fue generado automáticamente por el SGD COFAR.</p>
</div>""",
        "variables_json": VARS_COMUNES,
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
            print(f"  [+] {data['codigo'].value:30} - {data['nombre']!r}")
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
                print(f"  [~] {data['codigo'].value:30} actualizado")
                actualizados += 1
            else:
                print(f"  [=] {data['codigo'].value:30} sin cambios")
        await db.flush()
    return creados, actualizados


async def main() -> None:
    print("=" * 70)
    print("COFAR SGD - Seed Email Templates (US-9.04, sesion 13: 10 plantillas)")
    print("=" * 70)
    print(f"Total: {len(PLANTILLAS)} plantillas (10 del doc + 1 PDF)")

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
