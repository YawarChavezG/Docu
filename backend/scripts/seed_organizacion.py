"""
seed_organizacion.py — COFAR SGD (Sesion A, tarea #2)

Sembra las 27 areas faltantes del Excel "GERENCIAS, AREAS Y SIGLAS.xlsx"
para llegar a 49 areas totales (ya hay 23 sembradas por seed_data.py).

Origen de los datos: docs/Diagramas_Matrices/MATRICES/GERENCIAS, AREAS Y SIGLAS.xlsx
(leido con openpyxl y exportado a constantes aqui, sin dependencia runtime).

Uso (dentro del contenedor backend):
    docker exec sgd-backend python scripts/seed_organizacion.py

Idempotente: si un area ya existe (por sigla), la actualiza con nombre y gerencia.
NO duplica. Loggea cuantos creo vs cuantos actualizo.

Desviaciones del Excel original (documentadas):
  - LOG > SAC ("SISTEMA DE APOYO CRITICO, POR CONFIRMAR") se omite porque
    colisiona con COM > SAC ("SERVICIO DE ATENCION AL CLIENTE") y la sigla
    es UNIQUE global. La fila del Excel esta marcada POR CONFIRMAR.
  - TER > SISTEMAS sin sigla se omite (el Excel no le asigno sigla).
  - RRH > "ADMINISTRACION DE PERSONAL" sin sigla se omite (tambien POR CONFIRMAR).
  - ADM > "ADMINISTRACION" colisiona con RRH > ADM, pero como la unique es
    solo en areas.sigla (no en areas.gerencia_id+sigla), se permite.
"""
import asyncio
import sys
from pathlib import Path

# Make 'app' importable cuando se corre desde /app
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.area import Area
from app.models.gerencia import Gerencia


# (gerencia_sigla, sigla_area, nombre_area, orden)
AREAS_FALTANTES = [
    # ─── RECURSOS HUMANOS (1) ───
    ("RRH", "SGE", "SERVICIOS GENERALES", 4),

    # ─── ADMINISTRACION (4) ───
    # Mapeamos al sigil "ADM" del Excel aunque la BD usa "ADM" para ADMINISTRACION
    # (la unique en areas.sigla no choca con gerencias.sigla).
    ("ADM", "CON", "CONTABILIDAD", 1),
    ("ADM", "FIN", "FINANZAS", 2),
    ("ADM", "CO",  "COSTOS Y RENTABILIDAD", 3),
    ("ADM", "VIG", "VIGILANCIA Y SEGURIDAD INTERNA", 4),

    # ─── COMERCIAL (7) ───
    ("COM", "MKT", "MARKETING", 1),
    ("COM", "SAC", "SERVICIO DE ATENCION AL CLIENTE", 2),
    ("COM", "VTA", "VENTAS", 3),
    ("COM", "PC",  "PLANIFICACION COMERCIAL", 4),
    ("COM", "VM",  "VISITA MEDICA", 5),
    ("COM", "COF", "COMERCIAL OFICINA CENTRAL", 6),
    ("COM", "COR", "COMERCIAL OFICINA REGIONAL", 7),

    # ─── LOGISTICA (5) ───
    # OMITIDO: SAC "SISTEMA DE APOYO CRITICO" (colisiona con COM > SAC, POR CONFIRMAR en Excel).
    ("LOG", "PES", "PESAJE", 1),
    ("LOG", "MAN", "MANTENIMIENTO", 2),
    ("LOG", "CAL", "CALIBRACIONES", 3),
    ("LOG", "AMP", "ALMACEN MP", 4),
    ("LOG", "APT", "ALMACENES DE PRODUCTO TERMINADO", 5),

    # ─── TERCIA (1) ───
    # OMITIDO: SISTEMAS sin sigla en Excel.
    ("TER", "IT",  "INFRAESTRUCTURA TECNOLOGICA", 1),

    # ─── AUDITORIA INTERNA (1) ───
    ("AUD", "AI",  "AUDITORIA INTERNA", 1),

    # ─── GENERAL (3) ───
    ("GEN", "ETO", "EXCELENCIA Y TRANSFORMACION ORGANIZACIONAL", 1),
    ("GEN", "CCO", "COMUNICACION CORPORATIVA", 2),
    ("GEN", "AL",  "ASESORIA LEGAL", 3),

    # ─── OPERACIONES (5) ───
    ("OPS", "CPR", "COMPRAS", 1),
    ("OPS", "PI",  "PLANIFICACION INDUSTRIAL", 2),
    ("OPS", "INS", "INSTITUCIONES", 3),
    ("OPS", "GI",  "GESTION INDUSTRIAL", 4),
    ("OPS", "ART", "ARTES", 5),
]


async def _get_gerencia_cache(db: AsyncSession) -> dict[str, int]:
    """Carga el cache {sigla: id} de TODAS las gerencias existentes."""
    rows = (await db.execute(select(Gerencia))).scalars().all()
    return {g.sigla: g.id for g in rows}


async def seed_areas_faltantes(db: AsyncSession) -> tuple[int, int]:
    """
    Siembra las 27 areas faltantes.
    Retorna (creadas, actualizadas).
    """
    gerencias_cache = await _get_gerencia_cache(db)
    creadas = 0
    actualizadas = 0

    for gerencia_sigla, sigla, nombre, orden in AREAS_FALTANTES:
        gerencia_id = gerencias_cache.get(gerencia_sigla)
        if gerencia_id is None:
            print(
                f"  [!] SKIP {sigla} ({nombre}): gerencia '{gerencia_sigla}' "
                f"no existe. Ejecutar seed_data.py primero."
            )
            continue

        existing = (await db.execute(
            select(Area).where(Area.sigla == sigla)
        )).scalar_one_or_none()

        if existing is None:
            area = Area(
                gerencia_id=gerencia_id,
                sigla=sigla,
                nombre=nombre,
                orden=orden,
                activo=True,
            )
            db.add(area)
            print(f"  [+] Area creada: {sigla} ({gerencia_sigla}) - {nombre}")
            creadas += 1
        else:
            actualizo = False
            if existing.gerencia_id != gerencia_id:
                existing.gerencia_id = gerencia_id
                actualizo = True
            if existing.nombre != nombre:
                existing.nombre = nombre
                actualizo = True
            if existing.orden != orden:
                existing.orden = orden
                actualizo = True
            if not existing.activo:
                existing.activo = True
                actualizo = True
            if actualizo:
                print(f"  [~] Area actualizada: {sigla} ({gerencia_sigla})")
                actualizadas += 1
            else:
                print(f"  [=] Area sin cambios: {sigla} ({gerencia_sigla})")
        await db.flush()

    return creadas, actualizadas


async def main() -> None:
    print("=" * 70)
    print("COFAR SGD - Seed Organizacion (areas faltantes del Excel)")
    print("=" * 70)
    print(f"Total a sembrar: {len(AREAS_FALTANTES)} areas")

    async with AsyncSessionLocal() as db:
        try:
            print("\nSembrando areas faltantes...")
            creadas, actualizadas = await seed_areas_faltantes(db)
            await db.commit()

            print("\n" + "=" * 70)
            print(f"Resultado: {creadas} creadas, {actualizadas} actualizadas, "
                  f"{len(AREAS_FALTANTES) - creadas - actualizadas} sin cambios")
            print("=" * 70)
        except Exception as e:
            await db.rollback()
            print(f"\nError durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
