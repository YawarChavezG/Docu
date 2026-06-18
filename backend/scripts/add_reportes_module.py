"""
scripts/add_reportes_module.py — Sesion 25 / Issue 8.4.

Asigna el modulo REPORTES a todos los usuarios activos que:
- Tienen rol ELABORADOR - REVISOR
- Tienen rol ELABORADOR - REVISOR - APROBADOR
- NO tienen rol VISUALIZADOR (CL-EVAL)
- NO tienen rol ADMIN
- NO tienen el modulo TODOS (que es bypass)
- NO tienen ya el modulo REPORTES

Idempotente: ejecutar N veces no duplica asignaciones.

Uso:
    cd backend
    .venv\\Scripts\\python -m scripts.add_reportes_module [--dry-run] [--verbose]
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Path setup para importar app.*
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.modulo import CodigoModulo, Modulo
from app.models.rol import CodigoRol, Rol
from app.models.usuario import Usuario


# Roles que reciben el modulo REPORTES (cliente Issue 8.4)
ROLES_CON_REPORTES = {
    CodigoRol.ELABORADOR_REVISOR,
    CodigoRol.ELABORADOR_REVISOR_APROBADOR,
    # ETO tambien recibe REPORTES implicitamente (tiene TODOS), no necesita add
}

# Roles EXCLUIDOS (no se les agrega REPORTES)
ROLES_EXCLUIDOS = {
    CodigoRol.VISUALIZADOR_CL_EVAL,
    CodigoRol.ADMIN,
}


async def agregar_reportes(db: AsyncSession, dry_run: bool = False, verbose: bool = False):
    """
    Asigna el modulo REPORTES a usuarios elegibles. Retorna tupla
    (asignados, ya_lo_tenian, excluidos_por_rol, errores).
    """
    # 1) Obtener el modulo REPORTES
    mod_reportes = (await db.execute(
        select(Modulo).where(Modulo.codigo == CodigoModulo.REPORTES)
    )).scalar_one_or_none()
    if mod_reportes is None:
        print(f"ERROR: modulo {CodigoModulo.REPORTES.value} no existe en la BD.")
        return 0, 0, 0, 1

    # 2) Obtener roles excluidos
    roles_excluidos_rows = (await db.execute(
        select(Rol).where(Rol.codigo.in_([r.value for r in ROLES_EXCLUIDOS]))
    )).scalars().all()
    roles_excluidos_ids = {r.id for r in roles_excluidos_rows}

    # 3) Obtener modulos que son bypass (TODOS)
    mod_todos = (await db.execute(
        select(Modulo).where(Modulo.codigo == CodigoModulo.TODOS)
    )).scalar_one_or_none()
    mod_todos_id = mod_todos.id if mod_todos else None

    # 4) Iterar usuarios activos (con modulos y roles precargados para evitar
    # lazy load async en el loop)
    usuarios = (await db.execute(
        select(Usuario)
        .where(Usuario.estado == "activo")
        .options(
            selectinload(Usuario.modulos),
            selectinload(Usuario.roles),
        )
    )).scalars().all()

    asignados = 0
    ya_lo_tenian = 0
    excluidos_por_rol = 0
    errores = 0
    usuarios_evaluados = 0

    for u in usuarios:
        usuarios_evaluados += 1

        # Verificar si tiene TODOS (bypass)
        if mod_todos_id and any(m.id == mod_todos_id for m in u.modulos):
            excluidos_por_rol += 1
            if verbose:
                print(f"  SKIP {u.username}: tiene modulo TODOS (bypass)")
            continue

        # Verificar si tiene algun rol excluido
        if any(r.id in roles_excluidos_ids for r in u.roles):
            excluidos_por_rol += 1
            if verbose:
                roles_cod = [r.codigo for r in u.roles]
                print(f"  SKIP {u.username}: rol excluido {roles_cod}")
            continue

        # Verificar si tiene algun rol de los que reciben REPORTES
        tiene_rol_elegible = any(
            r.codigo in {rr.value for rr in ROLES_CON_REPORTES}
            for r in u.roles
        )
        if not tiene_rol_elegible:
            # Sin rol que aplique. Puede ser usuario sin rol (solicitante)
            # o rol no contemplado. Lo loggeamos solo en verbose.
            if verbose:
                roles_cod = [r.codigo for r in u.roles] or ["(sin rol)"]
                print(f"  SKIP {u.username}: rol no aplica {roles_cod}")
            continue

        # Verificar si ya tiene REPORTES
        if any(m.id == mod_reportes.id for m in u.modulos):
            ya_lo_tenian += 1
            if verbose:
                print(f"  SKIP {u.username}: ya tiene REPORTES")
            continue

        # ELEGIBLE: agregar REPORTES via la relationship.
        # u.modulos es una Mapped[List[Modulo]] con secondary=usuario_modulos,
        # asi que .append() hace el INSERT en la tabla N:M automaticamente.
        if not dry_run:
            try:
                u.modulos.append(mod_reportes)
                asignados += 1
                if verbose:
                    print(f"  +ADD {u.username} ({u.nombre_completo})")
            except Exception as e:
                errores += 1
                print(f"  ERROR {u.username}: {e}")
        else:
            asignados += 1
            if verbose:
                print(f"  +DRY {u.username} ({u.nombre_completo})")

    if not dry_run:
        await db.commit()
    else:
        await db.rollback()

    return asignados, ya_lo_tenian, excluidos_por_rol, errores, usuarios_evaluados


async def main():
    parser = argparse.ArgumentParser(
        description="Asigna el modulo REPORTES a usuarios elegibles (Issue 8.4)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Solo simular, no persistir")
    parser.add_argument("--verbose", action="store_true", help="Log detallado por usuario")
    args = parser.parse_args()

    print("=" * 60)
    print("Add REPORTES module (Issue 8.4)")
    print(f"  Modo: {'DRY-RUN' if args.dry_run else 'EJECUTAR'}")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        result = await agregar_reportes(db, dry_run=args.dry_run, verbose=args.verbose)
        if len(result) == 5:
            asignados, ya_lo_tenian, excluidos, errores, total = result
        else:
            return 1

    print("-" * 60)
    print(f"Usuarios evaluados:   {total}")
    print(f"Asignados:            {asignados}")
    print(f"Ya lo tenian:         {ya_lo_tenian}")
    print(f"Excluidos (rol):      {excluidos}")
    print(f"Errores:              {errores}")
    if args.dry_run:
        print("\n[DRY-RUN] No se persistio ningun cambio. Ejecutar sin --dry-run para aplicar.")
    return 0 if errores == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
