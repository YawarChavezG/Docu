"""
seed_feriados.py — COFAR SGD (Sesion A, tarea #6)

Sembra los 16 feriados oficiales de Bolivia 2026 + 2 departamentales La Paz/Santa Cruz.
(US-9.01 - calculo de plazos en dias habiles / calendario de bandejas).

Fuente: calendario oficial Bolivia 2026 (Decreto Supremo del Ministerio de Trabajo).
Nota: Carnaval y Viernes Santo son movibles; los del 2026 son:
  - Carnaval lunes 16-feb y martes 17-feb (confirmados por calendario 2026)
  - Viernes Santo viernes 3-abr ( Pascua 2026 = 5-abr, Viernes Santo = 3-abr )

Uso: docker exec sgd-backend python scripts/seed_feriados.py
Idempotente: si la fecha ya existe, actualiza nombre/tipo/departamento.
"""
import asyncio
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.feriado import Feriado, TipoFeriado


# (fecha, nombre, tipo, departamento_o_None)
FERIADOS_BOLIVIA_2026 = [
    # ─── Nacionales ───
    (date(2026, 1, 1),  "Ano Nuevo",                            TipoFeriado.NACIONAL,        None),
    (date(2026, 1, 22), "Dia del Estado Plurinacional de Bolivia", TipoFeriado.NACIONAL,        None),
    (date(2026, 2, 16), "Carnaval (Lunes)",                      TipoFeriado.NACIONAL,        None),
    (date(2026, 2, 17), "Carnaval (Martes)",                     TipoFeriado.NACIONAL,        None),
    (date(2026, 4, 3),  "Viernes Santo",                         TipoFeriado.NACIONAL,        None),
    (date(2026, 5, 1),  "Dia del Trabajo",                       TipoFeriado.NACIONAL,        None),
    (date(2026, 6, 2),  "Ano Nuevo Aymara (Willkakuti)",         TipoFeriado.NACIONAL,        None),
    (date(2026, 6, 21), "Ano Nuevo Andino Amazonico",            TipoFeriado.NACIONAL,        None),
    (date(2026, 8, 6),  "Dia de la Independencia de Bolivia",    TipoFeriado.NACIONAL,        None),
    (date(2026, 11, 2), "Dia de Todos los Santos (Difuntos)",    TipoFeriado.NACIONAL,        None),
    (date(2026, 12, 25),"Navidad",                               TipoFeriado.NACIONAL,        None),

    # ─── Departamentales ───
    (date(2026, 7, 16), "Dia del Departamento de La Paz",        TipoFeriado.DEPARTAMENTAL,   "LA PAZ"),
    (date(2026, 9, 24), "Dia del Departamento de Santa Cruz",    TipoFeriado.DEPARTAMENTAL,   "SANTA CRUZ"),
    (date(2026, 8, 10), "Dia del Departamento de Cochabamba",    TipoFeriado.DEPARTAMENTAL,   "COCHABAMBA"),
    (date(2026, 9, 14), "Dia del Departamento de Chuquisaca",    TipoFeriado.DEPARTAMENTAL,   "CHUQUISACA"),
    (date(2026, 11, 10),"Dia del Departamento de Pando",         TipoFeriado.DEPARTAMENTAL,   "PANDO"),
    (date(2026, 11, 15),"Dia del Departamento de Beni",          TipoFeriado.DEPARTAMENTAL,   "BENI"),
    (date(2026, 9, 6),  "Dia del Departamento de Tarija",        TipoFeriado.DEPARTAMENTAL,   "TARIJA"),
    (date(2026, 7, 17), "Dia del Departamento de Oruro",         TipoFeriado.DEPARTAMENTAL,   "ORURO"),
    (date(2026, 11, 18),"Dia del Departamento de Potosi",        TipoFeriado.DEPARTAMENTAL,   "POTOSI"),
]


async def seed_feriados(db: AsyncSession) -> tuple[int, int]:
    """Sembra los feriados. Retorna (creados, actualizados)."""
    creados = 0
    actualizados = 0

    for fecha, nombre, tipo, departamento in FERIADOS_BOLIVIA_2026:
        existing = (await db.execute(
            select(Feriado).where(Feriado.fecha == fecha)
        )).scalar_one_or_none()

        if existing is None:
            f = Feriado(
                fecha=fecha, nombre=nombre, tipo=tipo,
                departamento=departamento, activo=True,
            )
            db.add(f)
            print(f"  [+] {fecha} {nombre!r} ({tipo.value}, {departamento or '-'})")
            creados += 1
        else:
            changed = False
            if existing.nombre != nombre:
                existing.nombre = nombre
                changed = True
            if existing.tipo != tipo:
                existing.tipo = tipo
                changed = True
            if existing.departamento != departamento:
                existing.departamento = departamento
                changed = True
            if not existing.activo:
                existing.activo = True
                changed = True
            if changed:
                print(f"  [~] {fecha} {nombre!r} actualizado")
                actualizados += 1
            else:
                print(f"  [=] {fecha} {nombre!r} sin cambios")
        await db.flush()

    return creados, actualizados


async def main() -> None:
    print("=" * 70)
    print("COFAR SGD - Seed Feriados Bolivia 2026")
    print("=" * 70)
    print(f"Total: {len(FERIADOS_BOLIVIA_2026)} feriados "
          f"({sum(1 for f in FERIADOS_BOLIVIA_2026 if f[2] == TipoFeriado.NACIONAL)} nacionales, "
          f"{sum(1 for f in FERIADOS_BOLIVIA_2026 if f[2] == TipoFeriado.DEPARTAMENTAL)} departamentales)")

    async with AsyncSessionLocal() as db:
        try:
            creados, actualizados = await seed_feriados(db)
            await db.commit()
            print("\n" + "=" * 70)
            print(f"Resultado: {creados} creados, {actualizados} actualizados, "
                  f"{len(FERIADOS_BOLIVIA_2026) - creados - actualizados} sin cambios")
            print("=" * 70)
        except Exception as e:
            await db.rollback()
            print(f"\nError durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
