"""
Sesion 23 / Bloque B2: script CLI para ejecutar manualmente
`desactivar_ausencias_vencidas` sin esperar al cron 00:05.

Uso:
  docker exec sgd-backend python scripts/desactivar_ausencias_vencidas.py
  docker exec sgd-backend python scripts/desactivar_ausencias_vencidas.py --dry-run

El flag --dry-run muestra qué ausencias se desactivarian SIN hacer commit.
"""
import asyncio
import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.ausencia import Ausencia


async def main(dry_run: bool = False) -> None:
    hoy = date.today()
    async with AsyncSessionLocal() as db:
        stmt = select(Ausencia).where(
            Ausencia.activo == True,
            Ausencia.fecha_hasta < hoy,
        )
        rows = (await db.execute(stmt)).scalars().all()
        if not rows:
            print(f"[OK] No hay ausencias vencidas para desactivar (hoy={hoy}).")
            return
        print(f"Encontradas {len(rows)} ausencias vencidas (fecha_hasta < {hoy}):")
        for a in rows:
            print(f"  - id={a.id} usuario_id={a.usuario_id} {a.fecha_desde} -> {a.fecha_hasta} motivo={a.motivo!r} activo={a.activo}")
        if dry_run:
            print("\n[DRY-RUN] No se hicieron cambios.")
            return
        for a in rows:
            a.activo = False
        await db.commit()
        print(f"\n[OK] {len(rows)} ausencias desactivadas.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Desactivar ausencias vencidas")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar, no modificar")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
