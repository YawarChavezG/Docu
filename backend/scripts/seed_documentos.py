"""
seed_documentos.py
Sesion 21 R2 - Fase 1. Crea 10 documentos de ejemplo en la BD.

Idempotente: si se corre 2 veces, los (area, tipo, correlativo) ya existentes
se skipean (no duplica).

Reglas:
- Usa areas y tipos_documento reales de la BD.
- Crea UN DocumentoFlujo por cada Documento (estado ELABORACION para los
  no aprobados, FINALIZADO para los APROBADOS/OBSOLETOS).
- Distribuye estatus: 5 APROBADO, 2 EN_ELABORACION, 2 EN_REVISION, 1 OBSOLETO.
- Distribuye vigencia: 3+ VIGENTE, 2 POR_VENCER, 1 VENCIDO, 1 OBSOLETO.
- El unico VENCIDO tiene estatus=APROBADO (regla del usuario).
- Crea los archivos NO (storage stub en Fase 1, no se suben archivos reales).

Uso:
    docker exec sgd-backend python -m scripts.seed_documentos
"""
import asyncio
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Path setup para que funcione desde docker (el CWD es /app)
sys.path.insert(0, "/app")

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import AsyncSessionLocal
from app.models.area import Area
from app.models.documento import (
    Documento,
    EstatusDocumento,
    VigenciaDocumento,
)
from app.models.documento_flujo import (
    DocumentoFlujo,
    TipoSolicitud,
)
from app.models.estado import Estado
from app.models.tipo_documento import TipoDocumento
from app.models.usuario import Usuario
from app.services.correlativo_service import (
    formatear_codigo,
    siguiente_correlativo_advisory,
)


# ─── Datos de seed: (area_sigla, tipo_codigo_int, titulo, estatus, dias_atras, comentarios) ───
# Para tipos con periodo_vigencia=4 anos, dias_atras controla la vigencia final:
#   - dias_atras=120 → expira en ~1340 dias → VIGENTE
#   - dias_atras=1430 → expira en 30 dias → POR_VENCER
#   - dias_atras=1500 → expira hace 40 dias → VENCIDO
#   - dias_atras=1825 → VIGENTE hace mas de 4 anos, pero estatus=OBSOLETO → vigencia=OBSOLETO
SEED_DATA = [
    ("CC",   5, "Procedimiento de Control de Documentos del SIG",        EstatusDocumento.APROBADO,         120, "OK primera version"),
    ("DT",   3, "Politica de Direccion Tecnica",                        EstatusDocumento.APROBADO,          90, "Aprobado en sesion X"),
    ("EST",  7, "Especificacion de Estabilidad Acelerada",               EstatusDocumento.APROBADO,         180, "OK primera version"),
    # VENCIDO: aprobado hace 1500 dias, periodo 4 anos → ya expiro
    ("PRO",  5, "Procedimiento Operativo de Produccion",                 EstatusDocumento.APROBADO,        1500, "Aprobado en sesion X"),
    # POR_VENCER: aprobado hace 1430 dias → le quedan 30 dias
    ("BET",  7, "Especificacion de Betalactamicos",                     EstatusDocumento.APROBADO,        1430, "Aprobado en sesion X"),
    ("ACD",  5, "Procedimiento de Acondicionamiento",                    EstatusDocumento.EN_ELABORACION,   None, "Pendiente firma ETO"),
    ("VAL",  5, "Procedimiento de Validaciones",                         EstatusDocumento.EN_ELABORACION,   None, "Pendiente firma ETO"),
    ("REG",  4, "Plan Regulatorio 2026",                                 EstatusDocumento.EN_REVISION,      None, "OK primera version"),
    ("GAC",  3, "Politica de Garantia de Calidad",                       EstatusDocumento.EN_REVISION,      None, "Aprobado en sesion X"),
    # OBSOLETO: aprobado hace 5 anos, pero la vigencia es OBSOLETO por estatus
    ("MCB",  6, "Instructivo de Microbiologia - Version Antigua",        EstatusDocumento.OBSOLETO,        1825, "Documento reemplazado por v02"),
]


def calcular_vigencia_pura(
    estatus: EstatusDocumento,
    aprobacion_at,
    expira_at,
    tipo_indefinido: bool,
) -> VigenciaDocumento:
    """Version syncrona (sin tocar BD) de calcular_vigencia."""
    if estatus == EstatusDocumento.OBSOLETO:
        return VigenciaDocumento.OBSOLETO
    if aprobacion_at is None or expira_at is None:
        return VigenciaDocumento.VIGENTE
    if tipo_indefinido:
        return VigenciaDocumento.VIGENTE

    dias_restantes = (expira_at - datetime.now(timezone.utc)).days

    if dias_restantes < 0:
        if estatus in (EstatusDocumento.APROBADO, EstatusDocumento.OBSOLETO):
            return VigenciaDocumento.VENCIDO
        return VigenciaDocumento.VIGENTE

    if dias_restantes <= 5:
        return VigenciaDocumento.POR_VENCER

    if dias_restantes <= 30:
        return VigenciaDocumento.POR_VENCER

    return VigenciaDocumento.VIGENTE


async def seed():
    print("=" * 60)
    print("SEED DOCUMENTOS - Sesion 21 R2")
    print("=" * 60)

    inserted = 0
    skipped = 0
    errors = 0

    async with AsyncSessionLocal() as db:
        # ── 1. Cargar catalogos (1 query por catalogo) ──
        areas = (await db.execute(
            select(Area).where(Area.activo == True)
        )).scalars().all()
        areas_by_sigla = {a.sigla: a for a in areas}
        print(f"Areas activas: {len(areas)}")

        tipos = (await db.execute(
            select(TipoDocumento).where(TipoDocumento.activo == True)
        )).scalars().all()
        tipos_by_codigo = {t.codigo: t for t in tipos}
        print(f"Tipos activos: {len(tipos)}")

        elaborador = (await db.execute(
            select(Usuario).where(Usuario.username == "aromero")
        )).scalar_one_or_none()
        if not elaborador:
            print("[WARN] Usuario 'aromero' no existe. Usando id=1 si existe.")
            elaborador = (await db.execute(
                select(Usuario).where(Usuario.id == 1)
            )).scalar_one_or_none()
        elaborador_id = elaborador.id if elaborador else None
        elaborador_cargo = elaborador.cargo if elaborador else "Sin cargo"
        print(f"Elaborador: id={elaborador_id} cargo={elaborador_cargo!r}")

        estado_elab = (await db.execute(
            select(Estado).where(Estado.codigo == "ELABORACION")
        )).scalar_one_or_none()
        estado_final = (await db.execute(
            select(Estado).where(Estado.codigo == "FINALIZADO")
        )).scalar_one_or_none()
        if not estado_elab or not estado_final:
            print(f"[ERROR] Estados no encontrados (elab={estado_elab}, final={estado_final})")
            return
        print(f"Estados: ELABORACION={estado_elab.id} FINALIZADO={estado_final.id}")

        # ── 2. Insertar cada item del SEED_DATA ──
        for idx, (area_sigla, tipo_codigo, titulo, estatus, dias_atras, comentarios) in enumerate(SEED_DATA):
            try:
                area = areas_by_sigla.get(area_sigla)
                tipo = tipos_by_codigo.get(tipo_codigo)
                if not area:
                    print(f"  [SKIP] area {area_sigla!r} no existe")
                    skipped += 1
                    continue
                if not tipo:
                    print(f"  [SKIP] tipo {tipo_codigo} no existe")
                    skipped += 1
                    continue

                # Calcular correlativo con advisory lock
                correlativo = await siguiente_correlativo_advisory(db, area.id, tipo.id)
                codigo = formatear_codigo(area.sigla, tipo.codigo, correlativo)
                version = "00"

                # Verificar idempotencia ANTES de insertar.
                # Usamos (area, tipo, titulo) como clave estable: si ya existe
                # un documento con ese titulo en esa (area, tipo), skip.
                existing = (await db.execute(
                    select(Documento.id).where(
                        Documento.area_id == area.id,
                        Documento.tipo_documento_id == tipo.id,
                        Documento.titulo == titulo,
                    )
                )).scalar_one_or_none()
                if existing:
                    print(f"  [SKIP] {area_sigla}-{tipo_codigo} titulo={titulo[:30]!r} ya existe (doc_id={existing[0] if isinstance(existing, tuple) else existing})")
                    skipped += 1
                    continue

                # Fechas
                aprobacion_at = None
                expira_at = None
                if dias_atras is not None:
                    aprobacion_at = datetime.now(timezone.utc) - timedelta(days=dias_atras)
                    if not tipo.indefinido:
                        periodo = tipo.periodo_vigencia or 4
                        expira_at = aprobacion_at + timedelta(days=365 * periodo)

                # Vigencia (calculo en Python, sin tocar BD)
                vigencia = calcular_vigencia_pura(
                    estatus=estatus,
                    aprobacion_at=aprobacion_at,
                    expira_at=expira_at,
                    tipo_indefinido=tipo.indefinido,
                )

                # Crear Documento
                doc = Documento(
                    gerencia_id=area.gerencia_id,
                    area_id=area.id,
                    proceso_id=None,
                    tipo_documento_id=tipo.id,
                    correlativo=correlativo,
                    codigo=codigo,
                    version=version,
                    titulo=titulo,
                    aprobacion_at=aprobacion_at,
                    expira_at=expira_at,
                    vigencia=vigencia,
                    estatus=estatus,
                    codigo_antiguo=f"LEG-{area.id}-{tipo.id}-{idx+1:03d}",
                    comentarios_eto=comentarios[:50] if comentarios else None,
                    activo=True,
                    created_by_id=elaborador_id,
                    updated_by_id=elaborador_id,
                )
                db.add(doc)
                await db.flush()  # para obtener doc.id

                # Crear DocumentoFlujo
                estado_actual_id = (
                    estado_final.id if estatus in (EstatusDocumento.APROBADO, EstatusDocumento.OBSOLETO)
                    else estado_elab.id
                )
                flujo = DocumentoFlujo(
                    documento_id=doc.id,
                    estado_actual_id=estado_actual_id,
                    tipo_solicitud=TipoSolicitud.CREACION,
                    gerencia_id=area.gerencia_id,
                    area_id=area.id,
                    tipo_documento_id=tipo.id,
                    codigo_snapshot=codigo,
                    version_snapshot=version,
                    titulo=titulo,
                    elaborador_id=elaborador_id,
                    cargo_elaborador=elaborador_cargo,
                    fecha_solicitud=aprobacion_at or datetime.now(timezone.utc),
                    justificacion="Creacion inicial via seed_documentos.py",
                    tiempo_vigencia_anos=tipo.periodo_vigencia if not tipo.indefinido else None,
                    requiere_evaluacion=False,
                    requiere_control_lectura=False,
                    alcance_difusion_ids=[area.gerencia_id],
                    revisor_ids=[elaborador_id] if elaborador_id else [],
                    aprobador_ids=[elaborador_id] if elaborador_id else [],
                    reemplaza_documento_ids=None,
                    firma_usuario_id=elaborador_id,
                    firma_at=aprobacion_at or datetime.now(timezone.utc),
                    firma_ip="127.0.0.1",
                    firma_user_agent="seed_documentos.py",
                    activo=True,
                    created_by_id=elaborador_id,
                )
                db.add(flujo)
                await db.commit()

                print(
                    f"  [OK] {doc.codigo_completo} - {titulo[:40]:40s} | "
                    f"estatus={estatus.value:14s} vigencia={vigencia.value}"
                )
                inserted += 1

            except IntegrityError as e:
                await db.rollback()
                print(f"  [SKIP-INT] ({area_sigla}, {tipo_codigo}): {str(e.orig)[:80]}")
                skipped += 1
            except Exception as e:
                await db.rollback()
                print(f"  [ERROR] ({area_sigla}, {tipo_codigo}): {type(e).__name__}: {str(e)[:100]}")
                errors += 1

    print("=" * 60)
    print(f"Inserted: {inserted} | Skipped: {skipped} | Errors: {errors}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
