"""
seed_plantillas_db.py — COFAR SGD (R3 Fase 1, sesion 38)

Migra las plantillas documentales del filesystem a la tabla `plantillas`.
Idempotente: usa seed_plantillas_desde_disco() que salta archivos ya migrados.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import AsyncSessionLocal
from app.services.plantilla_manager_service import seed_plantillas_desde_disco


async def main() -> None:
    print("=" * 70)
    print("COFAR SGD - Seed Plantillas DB (migracion filesystem -> BD)")
    print("=" * 70)

    async with AsyncSessionLocal() as db:
        try:
            count = await seed_plantillas_desde_disco(db)
            await db.commit()
            print(f"Resultado: {count} plantillas migradas a BD")
            print("=" * 70)
        except Exception as e:
            await db.rollback()
            print(f"\nError durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
