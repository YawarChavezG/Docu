"""
seed_matriz_eto.py — COFAR SGD (Sesion A, tarea #8)

Sembra la matriz de enrutamiento ETO (US-9.03 sub-tarjeta 3):
  - 2 analistas ETO: Aracely Romero (ya existe, user_id=1) y Cecilia Espinoza (se crea)
  - 10 gerencias asignadas segun el Excel 'ASIGNACION AUTOMATICA ANALISTAS ETO.xlsx'

Uso: docker exec sgd-backend python scripts/seed_matriz_eto.py
Idempotente: si la fila de la gerencia ya existe, la actualiza. Si la matriz
queda vacia, se siembra desde cero.

Crea el usuario cecEspinoza (rol ETO + modulo TODOS) si no existe.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.gerencia import Gerencia
from app.models.matriz_enrutamiento_eto import (
    MatrizEnrutamientoEto, DisponibilidadEto,
)
from app.models.modulo import CodigoModulo, Modulo
from app.models.rol import CodigoRol, Rol
from app.models.usuario import (
    EstadoDelegacion, EstadoUsuario, Usuario, usuario_roles,
)


# (sigla_gerencia, username_analista)
ASIGNACIONES = [
    ("ADM",   "cecEspinoza"),
    ("AUD",   "cecEspinoza"),
    ("CAL",   "aromero"),
    ("COM",   "cecEspinoza"),
    ("GEN",   "aromero"),
    ("LOG",   "cecEspinoza"),
    ("OPS",   "cecEspinoza"),
    ("PLA",   "aromero"),
    ("RRH",   "cecEspinoza"),
    ("TER",   "aromero"),
]


async def _ensure_cecEspinoza(db: AsyncSession) -> int:
    """Crea el usuario cecEspinoza (rol ETO) si no existe. Devuelve user_id."""
    existing = (await db.execute(
        select(Usuario).where(Usuario.username == "cecEspinoza")
    )).scalar_one_or_none()
    if existing is not None:
        print(f"  [=] Usuario cecEspinoza ya existe (id={existing.id})")
        return existing.id

    # Necesita rol ETO
    rol_eto = (await db.execute(
        select(Rol).where(Rol.codigo == CodigoRol.ETO)
    )).scalar_one_or_none()
    if rol_eto is None:
        raise RuntimeError("Rol ETO no existe. Ejecutar seed_data.py primero.")

    u = Usuario(
        username="cecEspinoza",
        email="cecEspinoza@cofar.local",
        nombre_completo="Cecilia Espinoza",
        iniciales="CE",
        cargo="Gestor Documental ETO",
        area_id=None,  # el seed_organizacion no asigna ETOs a un area especifica
        azure_oid=None,
        ad_info=None,
        ad_postal_code=None,
        ad_last_synced_at=None,
        estado=EstadoUsuario.ACTIVO,
        ausente=False,
        estado_delegacion=EstadoDelegacion.NA,
    )
    db.add(u)
    await db.flush()
    print(f"  [+] Usuario cecEspinoza creado (id={u.id})")

    # Asignar rol ETO
    await db.execute(usuario_roles.insert().values(usuario_id=u.id, rol_id=rol_eto.id))
    # Sesion 26: modulo por usuario eliminado (era codigo muerto).
    # El control de acceso es por ROL via ACL hardcodeado en el frontend
    # (auth.js:canAccess).
    print(f"      rol=ETO")
    return u.id


async def _seed_matriz(db: AsyncSession, username_to_id: dict[str, int]) -> tuple[int, int]:
    creadas = 0
    actualizadas = 0
    for sigla, username in ASIGNACIONES:
        ger = (await db.execute(
            select(Gerencia).where(Gerencia.sigla == sigla)
        )).scalar_one_or_none()
        if ger is None:
            print(f"  [!] SKIP {sigla}: gerencia no existe. Ejecutar seed_data.py primero.")
            continue

        analista_id = username_to_id.get(username)
        if analista_id is None:
            print(f"  [!] SKIP {sigla}: usuario {username!r} no existe")
            continue

        existing = (await db.execute(
            select(MatrizEnrutamientoEto).where(MatrizEnrutamientoEto.gerencia_id == ger.id)
        )).scalar_one_or_none()

        if existing is None:
            m = MatrizEnrutamientoEto(
                gerencia_id=ger.id,
                analista_usuario_id=analista_id,
                disponibilidad=DisponibilidadEto.DISPONIBLE,
                delegado_usuario_id=None,
            )
            db.add(m)
            print(f"  [+] {sigla:5} -> {username} (analista_id={analista_id})")
            creadas += 1
        else:
            changed = False
            if existing.analista_usuario_id != analista_id:
                existing.analista_usuario_id = analista_id
                changed = True
            if changed:
                print(f"  [~] {sigla:5} -> {username} (actualizada)")
                actualizadas += 1
            else:
                print(f"  [=] {sigla:5} -> {username} (sin cambios)")
        await db.flush()
    return creadas, actualizadas


async def main() -> None:
    print("=" * 70)
    print("COFAR SGD - Seed Matriz Enrutamiento ETO (US-9.03)")
    print("=" * 70)
    print(f"Total: {len(ASIGNACIONES)} gerencias -> 2 analistas ETO")

    async with AsyncSessionLocal() as db:
        try:
            # 1. Asegurar que cecEspinoza existe
            cec_id = await _ensure_cecEspinoza(db)
            await db.flush()

            # 2. Cargar IDs de los analistas
            aromero = (await db.execute(
                select(Usuario).where(Usuario.username == "aromero")
            )).scalar_one_or_none()
            if aromero is None:
                raise RuntimeError("Usuario aromero no existe. Ejecutar seed_data.py primero.")
            username_to_id = {"aromero": aromero.id, "cecEspinoza": cec_id}

            # 3. Sembrar la matriz
            creadas, actualizadas = await _seed_matriz(db, username_to_id)
            await db.commit()

            print("\n" + "=" * 70)
            print(f"Resultado: {creadas} creadas, {actualizadas} actualizadas")
            print("=" * 70)
        except Exception as e:
            await db.rollback()
            print(f"\nError durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
