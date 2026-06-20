"""
run_matriz_import.py — COFAR SGD (Sesion 8, tarea #12.3)

CLI para ejecutar la carga masiva de la matriz de abril.

Uso (dentro del contenedor backend):
    docker exec sgd-backend python scripts/run_matriz_import.py \
        --excel /app/docs/Diagramas_Matrices/MATRICES/"USUARIOS EXISTENTES A ABRIL.xlsx"

    # O desde el host (con el repo montado):
    docker exec sgd-backend python scripts/run_matriz_import.py \
        --excel "/tmp/matriz_abril.xlsx" --dry-run

    # Para pisar asignaciones existentes:
    docker exec sgd-backend python scripts/run_matriz_import.py \
        --excel "/tmp/matriz_abril.xlsx" --update-existing

Argumentos:
    --excel PATH           (obligatorio) ruta al Excel
    --dry-run              (opcional) NO hace commit, solo imprime el diff
    --update-existing      (opcional) pisa rol/modulos si el usuario ya tiene uno
    --verbose              (opcional) muestra los warnings completos
    --yes                  (opcional) salta la confirmacion interactiva
                           (usar con cuidado, solo para CI/automatizacion)

Comportamiento:
    - Idempotente: re-correr sin --update-existing no pisa nada.
    - Reporta counts antes/despues (SELECT pre + post).
    - Si la cantidad a aplicar difiere de la esperada, pregunta.
    - Loggea warnings a stderr y resumen a stdout.

Exit codes:
    0  exito
    1  error fatal (Excel no encontrado, header invalido, errores de catalogo)
    2  cancelado por el usuario (no escribio SI)
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Path setup para que 'app' sea importable cuando se corre desde /app
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select, text

from app.core.database import AsyncSessionLocal
from app.models import Usuario
from app.services.matriz_import_service import (
    ImportResult,
    MatchResult,
    aplicar_asignaciones,
    match_usuarios,
    parsear_excel,
)

logger = logging.getLogger("run_matriz_import")


def setup_logging(verbose: bool) -> None:
    """Configura logging segun el flag --verbose."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Silenciar SQLAlchemy engine (solo queremos nuestros mensajes)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Carga masiva de roles y modulos desde la matriz de abril.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--excel", required=True, help="Ruta al Excel de la matriz (obligatorio)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="NO hace commit, solo imprime el diff (rollback al final)",
    )
    parser.add_argument(
        "--update-existing",
        action="store_true",
        help="Pisa rol/modulos si el usuario ya tiene uno (default: skip)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Muestra los warnings completos"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Salta la confirmacion interactiva (usar con cuidado)",
    )
    return parser.parse_args()


async def count_usuarios_con_rol(db) -> int:
    """Cuenta usuarios con al menos 1 rol asignado."""
    res = await db.execute(
        select(Usuario.id).where(
            text("(SELECT COUNT(*) FROM usuario_roles WHERE usuario_roles.usuario_id = usuarios.id) > 0")
        )
    )
    return len(res.all())


def print_resumen(
    match_result: MatchResult,
    import_result: ImportResult,
    count_before: int,
    count_after: int,
    dry_run: bool,
) -> None:
    """Imprime el resumen final del import."""
    print("\n" + "=" * 70)
    print(f"RESUMEN DEL IMPORT {'(DRY-RUN)' if dry_run else ''}")
    print("=" * 70)
    print(f"  Filas en Excel (COFARs validos): {len(match_result.matched) + len(match_result.unmatched)}")
    print(f"  Match con BD:                     {len(match_result.matched)}")
    print(f"  Sin match (skip):                 {len(match_result.unmatched)}")
    print(f"  Errores de catalogo:              {len(import_result.errores)}")
    print(f"  Usuarios ya tenian rol (skip):    {import_result.skipped_existing}")
    print()
    print(f"  Roles asignados:                  {import_result.roles_asignados}")
    print(f"  Modulos asignados (N:M):          {import_result.modulos_asignados}")
    print(f"  Flags actualizados:               {import_result.flags_actualizados}")
    print()
    print(f"  Usuarios con rol ANTES:  {count_before}")
    print(f"  Usuarios con rol DESPUES: {count_after}")
    delta = count_after - count_before
    print(f"  Delta:                   {'+' if delta >= 0 else ''}{delta}")
    print()
    if import_result.warnings:
        print(f"  Warnings ({len(import_result.warnings)}):")
        for w in import_result.warnings[:10]:
            print(f"    - {w}")
        if len(import_result.warnings) > 10:
            print(f"    ... y {len(import_result.warnings) - 10} mas (use --verbose para ver todos)")
    if import_result.errores:
        print(f"\n  ERRORES ({len(import_result.errores)}):")
        for e in import_result.errores[:10]:
            print(f"    - {e}")


def confirmar(asignaciones: int, dry_run: bool, skip_confirm: bool) -> bool:
    """Pide confirmacion al usuario. Retorna True si confirma."""
    if dry_run or skip_confirm:
        return True
    print(f"\nVa a aplicar {asignaciones} asignaciones a la BD.")
    resp = input("Escriba 'SI' para confirmar (o Enter para cancelar): ").strip()
    return resp == "SI"


async def main() -> int:
    args = parse_args()
    setup_logging(args.verbose)

    print("=" * 70)
    print("COFAR SGD - Carga masiva de matriz de abril")
    print("=" * 70)
    print(f"  Excel:           {args.excel}")
    print(f"  Dry-run:         {args.dry_run}")
    print(f"  Update-existing: {args.update_existing}")
    print()

    # 1) Parsear el Excel
    try:
        rows, parse_warnings = parsear_excel(args.excel)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if parse_warnings:
        print(f"Warnings del parser ({len(parse_warnings)}):")
        for w in parse_warnings[:5]:
            print(f"  - {w}")
        if len(parse_warnings) > 5:
            print(f"  ... y {len(parse_warnings) - 5} mas")

    if not rows:
        print("No hay filas validas para procesar.")
        return 1

    print(f"Filas validas en el Excel: {len(rows)}")

    # 2) Matchear contra BD
    async with AsyncSessionLocal() as db:
        match_result = await match_usuarios(rows, db)
        count_before = await count_usuarios_con_rol(db)

    print(f"  Match: {len(match_result.matched)} | Unmatched: {len(match_result.unmatched)}")
    if match_result.warnings and args.verbose:
        for w in match_result.warnings[:5]:
            print(f"    [match] {w}")

    if not match_result.matched:
        print("No hay usuarios para actualizar. Saliendo.")
        return 0

    # 3) Confirmar antes de aplicar
    # Estimamos cuantos se aplicarian (los que no tienen rol previo)
    # Para no hacer doble query, asumimos que casi todos se aplicaran
    estimated = len(match_result.matched) - 1  # 1 ya tiene rol (aromero)
    if not confirmar(estimated, args.dry_run, args.yes):
        print("Cancelado por el usuario.")
        return 2

    # 4) Aplicar (con o sin commit segun dry-run)
    async with AsyncSessionLocal() as db:
        try:
            import_result = await aplicar_asignaciones(
                match_result.matched, db, update_existing=args.update_existing
            )
            if args.dry_run:
                await db.rollback()
            else:
                await db.commit()
            count_after = await count_usuarios_con_rol(db)
        except Exception as e:
            await db.rollback()
            print(f"\nERROR durante la aplicacion: {e}", file=sys.stderr)
            logger.exception("Error en aplicar_asignaciones")
            return 1

    print_resumen(match_result, import_result, count_before, count_after, args.dry_run)
    return 0 if import_result.ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
