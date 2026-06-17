"""
seed_tipos_documento.py — COFAR SGD (Sesion A, tarea #9b, refactor sesion 13)

Sembra los 13 tipos de documento del Excel 'TIPOS DE DOCUMENTO, CODIGO Y VIGENCIA.xlsx'.

REFACTOR sesion 13 (2026-06-16):
  - `codigo` ahora es int (1-14), UNIQUE
  - `slug` es str MAYUSCULAS, UNIQUE (lo que antes era el campo `codigo`)
  - `nombre` UNIQUE
  - `codigo_doc` se elimina del modelo

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


# (codigo_int, slug, nombre, periodo_vigencia_o_None, observacion_o_None)
TIPOS = [
    (1,  "METODOLOGIA",           "Metodologia",                 4,    None),
    (2,  "MANUAL_FUNCIONES",      "Manual de Funciones",         None, "INDEFINIDO"),
    (3,  "POLITICA",              "Politica",                    4,    None),
    (4,  "PLAN",                  "Plan",                        4,    None),
    (5,  "PROCEDIMIENTO",         "Procedimiento",               4,    None),
    (6,  "INSTRUCTIVO",           "Instructivo",                 4,    None),
    (6,  "INSTRUCTIVO_TECNICO",   "Instructivo Tecnico",         None, "SOLO APLICA PARA MANTENIMIENTO"),
    (7,  "ESPECIFICACION",        "Especificacion",              4,    None),
    (9,  "PROTOCOLO",             "Protocolo",                   None, "INDEFINIDO"),
    (10, "MANUAL_PROCESO",        "Manual de Proceso",           4,    None),
    (12, "MANUAL",                "Manual",                      4,    None),
    (13, "MANUAL_USUARIO",        "Manuales de Usuario",         None, "INDEFINIDO"),
    (14, "FICHA_CARACTERIZACION", "Ficha de Caracterizacion",    4,    None),
]


async def seed_tipos(db: AsyncSession) -> tuple[int, int]:
    creados = 0
    actualizados = 0
    for codigo_int, slug, nombre, periodo, obs in TIPOS:
        indefinido = periodo is None
        # match por codigo int (unico) o por slug (unico) para idempotencia
        existing = (await db.execute(
            select(TipoDocumento).where(
                (TipoDocumento.codigo == codigo_int) | (TipoDocumento.slug == slug)
            )
        )).scalar_one_or_none()

        if existing is None:
            t = TipoDocumento(
                codigo=codigo_int, slug=slug, nombre=nombre,
                periodo_vigencia=periodo, indefinido=indefinido,
                max_descargas_dia=10,  # default US-9.02
                observacion=obs, activo=True,
            )
            db.add(t)
            vig = "INDEF" if indefinido else f"{periodo}a"
            print(f"  [+] codigo={codigo_int:2} slug={slug:25} {vig:5} {obs or ''}")
            creados += 1
        else:
            changed = False
            if existing.codigo != codigo_int:
                existing.codigo = codigo_int; changed = True
            if existing.slug != slug:
                existing.slug = slug; changed = True
            if existing.nombre != nombre:
                existing.nombre = nombre; changed = True
            if existing.periodo_vigencia != periodo:
                existing.periodo_vigencia = periodo; changed = True
            if existing.indefinido != indefinido:
                existing.indefinido = indefinido; changed = True
            if existing.observacion != obs:
                existing.observacion = obs; changed = True
            if not existing.activo:
                existing.activo = True; changed = True
            if changed:
                print(f"  [~] codigo={codigo_int:2} slug={slug:25} actualizado")
                actualizados += 1
            else:
                print(f"  [=] codigo={codigo_int:2} slug={slug:25} sin cambios")
        await db.flush()
    return creados, actualizados


async def main() -> None:
    print("=" * 70)
    print("COFAR SGD - Seed Tipos de Documento (US-9.03 sub-1)")
    print("=" * 70)
    print(f"Total: {len(TIPOS)} tipos del Excel (REFACTOR sesion 13)")

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
