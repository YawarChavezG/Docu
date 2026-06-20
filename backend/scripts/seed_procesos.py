"""
seed_procesos.py — COFAR SGD (R3 Fase 1, sesion 37)

Sembra 10 procesos genericos en la tabla `procesos`.
PROPUESTA-R3-TABLAS.md §1.5.6.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.proceso import Proceso


PROCESOS = [
    "Analisis",
    "Capacitacion",
    "Compras",
    "Fabricacion",
    "Investigacion",
    "Logistica",
    "Mantenimiento",
    "Produccion",
    "Seguridad",
    "Ventas",
]


async def seed_procesos(db: AsyncSession) -> int:
    creados = 0
    for nombre in PROCESOS:
        existing = (await db.execute(
            select(Proceso).where(Proceso.nombre == nombre)
        )).scalar_one_or_none()
        if existing is None:
            p = Proceso(nombre=nombre, activo=True)
            db.add(p)
            print(f"  [+] {nombre}")
            creados += 1
        else:
            if not existing.activo:
                existing.activo = True
                print(f"  [~] {nombre} reactivado")
            else:
                print(f"  [=] {nombre} ya existe")
        await db.flush()
    return creados


async def main() -> None:
    print("=" * 70)
    print("COFAR SGD - Seed Procesos (R3 Fase 1)")
    print("=" * 70)
    print(f"Total: {len(PROCESOS)} procesos genericos")

    async with AsyncSessionLocal() as db:
        try:
            creados = await seed_procesos(db)
            await db.commit()
            print("\n" + "=" * 70)
            print(f"Resultado: {creados} creados")
            print("=" * 70)
        except Exception as e:
            await db.rollback()
            print(f"\nError durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
