"""
seed_tipos_documento.py — COFAR SGD (Sesion A, tarea #9b)

Sembra los 13 tipos de documento del Excel 'TIPOS DE DOCUMENTO, C\xd3DIGO Y VIGENCIA.xlsx'.

Uso: docker exec sgd-backend python scripts/seed_tipos_documento.py
Idempotente.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.tipo_documento import TipoDocumento


# (codigo, nombre, codigo_doc, periodo_vigencia_o_None, observacion_o_None)
TIPOS = [
    ("METODOLOGIA",             "Metodologia",                 1,  4,    None),
    ("MANUAL_FUNCIONES",        "Manual de Funciones",         2,  None, "INDEFINIDO"),
    ("POLITICA",                "Politica",                    3,  4,    None),
    ("PLAN",                    "Plan",                        4,  4,    None),
    ("PROCEDIMIENTO",           "Procedimiento",               5,  4,    None),
    ("INSTRUCTIVO",             "Instructivo",                 6,  4,    None),
    ("INSTRUCTIVO_TECNICO",     "Instructivo Tecnico",         6,  None, "SOLO APLICA PARA MANTENIMIENTO"),
    ("ESPECIFICACION",          "Especificacion",              7,  4,    None),
    ("PROTOCOLO",               "Protocolo",                   9,  None, "INDEFINIDO"),
    ("MANUAL_PROCESO",          "Manual de Proceso",          10,  4,    None),
    ("MANUAL",                  "Manual",                     12,  4,    None),
    ("MANUAL_USUARIO",          "Manuales de Usuario",        13,  None, "INDEFINIDO"),
    ("FICHA_CARACTERIZACION",   "Ficha de Caracterizacion",  14,  4,    None),
]


async def seed_tipos(db: AsyncSession) -> tuple[int, int]:
    creados = 0
    actualizados = 0
    for codigo, nombre, codigo_doc, periodo, obs in TIPOS:
        indefinido = periodo is None
        existing = (await db.execute(
            select(TipoDocumento).where(TipoDocumento.codigo == codigo)
        )).scalar_one_or_none()

        if existing is None:
            t = TipoDocumento(
                codigo=codigo, nombre=nombre, codigo_doc=codigo_doc,
                periodo_vigencia=periodo, indefinido=indefinido,
                max_descargas_dia=10,  # default US-9.02
                observacion=obs, activo=True,
            )
            db.add(t)
            vig = "INDEF" if indefinido else f"{periodo}a"
            print(f"  [+] {codigo:25} (cod_doc={codigo_doc:2}) {vig:5} {obs or ''}")
            creados += 1
        else:
            changed = False
            if existing.nombre != nombre:
                existing.nombre = nombre; changed = True
            if existing.codigo_doc != codigo_doc:
                existing.codigo_doc = codigo_doc; changed = True
            if existing.periodo_vigencia != periodo:
                existing.periodo_vigencia = periodo; changed = True
            if existing.indefinido != indefinido:
                existing.indefinido = indefinido; changed = True
            if existing.observacion != obs:
                existing.observacion = obs; changed = True
            if not existing.activo:
                existing.activo = True; changed = True
            if changed:
                print(f"  [~] {codigo:25} actualizado")
                actualizados += 1
            else:
                print(f"  [=] {codigo:25} sin cambios")
        await db.flush()
    return creados, actualizados


async def main() -> None:
    print("=" * 70)
    print("COFAR SGD - Seed Tipos de Documento (US-9.03 sub-1)")
    print("=" * 70)
    print(f"Total: {len(TIPOS)} tipos del Excel")

    async with AsyncSessionLocal() as db:
        try:
            creados, actualizados = await seed_tipos(db)
            await db.commit()
            print("\n" + "=" * 70)
            print(f"Resultado: {creados} creados, {actualizados} actualizados")
            print("=" * 70)
        except Exception as e:
            await db.rollback()
            print(f"\nError durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
