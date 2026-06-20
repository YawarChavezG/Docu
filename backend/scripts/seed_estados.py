"""
seed_estados.py — COFAR SGD (Sesion A, tarea #9c)

Sembra los 5 estados del flujo (US-9.03 sub-tarjeta 2):
  ELABORACION -> LIBERACION_ETO -> REVISION_PARALELA -> FINALIZADO
  ANULADO (estado terminal alternativo)
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.estado import Estado, ContextoEstado


# (codigo, nombre, contexto, orden, descripcion)
ESTADOS = [
    ("ELABORACION",       "Elaboracion",       ContextoEstado.PROCESO, 1, "Estado inicial del documento. Creador trabajando en el borrador."),
    ("LIBERACION_ETO",    "Liberacion ETO",    ContextoEstado.PROCESO, 2, "Documento pasa por control de calidad de la oficina ETO antes de liberarse a revisores."),
    ("REVISION_PARALELA", "Revision Paralela", ContextoEstado.PROCESO, 3, "Multiples revisores aprueban en paralelo. Termina cuando todos completan o cuando se fuerza la finalizacion."),
    ("FINALIZADO",        "Finalizado",        ContextoEstado.PROCESO, 4, "Documento aprobado y publicado en Lista Maestra."),
    ("ANULADO",           "Anulado",           ContextoEstado.PROCESO, 5, "Documento cancelado antes de su aprobacion. Estado terminal alternativo."),
]


async def seed_estados(db: AsyncSession) -> tuple[int, int]:
    creados = 0
    actualizados = 0
    for codigo, nombre, contexto, orden, desc in ESTADOS:
        existing = (await db.execute(
            select(Estado).where(Estado.codigo == codigo)
        )).scalar_one_or_none()

        if existing is None:
            e = Estado(codigo=codigo, nombre=nombre, contexto=contexto,
                       orden=orden, descripcion=desc, activo=True)
            db.add(e)
            print(f"  [+] {codigo:20} {nombre:25} ({contexto.value})")
            creados += 1
        else:
            changed = False
            if existing.nombre != nombre: existing.nombre = nombre; changed = True
            if existing.contexto != contexto: existing.contexto = contexto; changed = True
            if existing.orden != orden: existing.orden = orden; changed = True
            if existing.descripcion != desc: existing.descripcion = desc; changed = True
            if not existing.activo: existing.activo = True; changed = True
            if changed:
                print(f"  [~] {codigo:20} actualizado")
                actualizados += 1
            else:
                print(f"  [=] {codigo:20} sin cambios")
        await db.flush()
    return creados, actualizados


async def main() -> None:
    print("=" * 70)
    print("COFAR SGD - Seed Estados (US-9.03 sub-2)")
    print("=" * 70)
    print(f"Total: {len(ESTADOS)} estados del flujo")

    async with AsyncSessionLocal() as db:
        try:
            creados, actualizados = await seed_estados(db)
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
