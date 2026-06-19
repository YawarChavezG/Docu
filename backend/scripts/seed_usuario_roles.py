"""
seed_usuario_roles.py — COFAR SGD (Sesion 33, deploy v1.1.0-qas)

Sembra las asignaciones de roles de los ~750 usuarios del AD de COFAR que
fueron asignados manualmente en DES (750+ filas en `usuario_roles`).

Por que existe este script:
  - En DES, los roles se asignaron con `run_matriz_import.py` desde el Excel
    "USUARIOS EXISTENTES A ABRIL.xlsx" (sesion 8, ~716 usuarios, 3312 modulos).
    El `usuario_modulos` se elimino en sesion 26 pero `usuario_roles` se
    preservo y crecio a ~729 filas tras las correcciones de sesion 23-32.
  - En QAS, un fresh-install solo crea 4 usuarios stub (seed_data.py). Los
    750+ usuarios del AD se sincronizan con el sync AD, pero arrancan con
    rol `visualizador` por default. Sin este seed, nadie tiene permisos
    para operar (todos visualizador).
  - Re-correr `run_matriz_import.py` requiere el Excel matriz (que solo
    esta en DES). Este seed extrae la snapshot de las 729 filas como
    INSERTs idempotentes.

Uso:
    docker exec sgd-qas-backend python scripts/seed_usuario_roles.py
    # o
    cd backend && .venv/Scripts/python scripts/seed_usuario_roles.py

Idempotencia:
  - Cada INSERT usa `ON CONFLICT (usuario_id, rol_id) DO NOTHING`.
  - La PK de `usuario_roles` es exactamente (usuario_id, rol_id), asi que
    el ON CONFLICT es seguro.
  - Re-correr el script multiples veces NO causa errores ni duplicados.
  - Si un usuario no existe (no fue sincronizado del AD todavia), el FK
    falla. El script reporta esos casos al final.

Salida esperada: 729 filas insertadas (o 0 si ya estaban).
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal


SQL_FILE = Path(__file__).resolve().parent / "seed_usuario_roles.sql"


async def main() -> None:
    if not SQL_FILE.exists():
        print(f"[ERROR] No se encontro {SQL_FILE}")
        sys.exit(1)

    sql_text = SQL_FILE.read_text(encoding="utf-8")
    # Contar statements (cada linea es un INSERT)
    inserts = [ln.strip() for ln in sql_text.splitlines() if ln.strip().startswith("INSERT")]
    total = len(inserts)
    print("=" * 70)
    print("COFAR SGD - Seed usuario_roles (snapshot 729 filas, sesion 33)")
    print("=" * 70)
    print(f"Archivo: {SQL_FILE.name} ({total} INSERTs ON CONFLICT DO NOTHING)")

    async with AsyncSessionLocal() as db:
        try:
            # Count ANTES
            count_before = (await db.execute(
                text("SELECT count(*) FROM usuario_roles")
            )).scalar_one()
            print(f"\n  Antes:   {count_before} filas en usuario_roles")

            # asyncpg (y por lo tanto SQLAlchemy async) NO soporta multiples
            # statements en una sola prepared statement. Hay que ejecutar
            # cada INSERT por separado. 729 INSERTs tarda ~1-2s, es OK.
            for i, stmt in enumerate(inserts, 1):
                await db.execute(text(stmt))
            await db.commit()

            # Count DESPUES
            count_after = (await db.execute(
                text("SELECT count(*) FROM usuario_roles")
            )).scalar_one()
            delta = count_after - count_before
            print(f"  Despues:  {count_after} filas en usuario_roles")
            print(f"  Nuevas:   {delta} (esperado ~{total} en fresh-install, 0 si ya estaban)")

            # Conteo por rol (sanidad)
            print("\n  Distribucion por rol:")
            rows = (await db.execute(text("""
                SELECT r.codigo, count(ur.*) AS n
                FROM roles r
                LEFT JOIN usuario_roles ur ON ur.rol_id = r.id
                GROUP BY r.codigo
                ORDER BY r.codigo
            """))).all()
            for codigo, n in rows:
                print(f"    {codigo:35s} {n:4d}")

            print("\n" + "=" * 70)
            print(f"OK: {delta} nuevas asignaciones creadas (idempotente).")
            print("=" * 70)
        except Exception as e:
            await db.rollback()
            err = str(e)
            # Si el error es un FK (usuario no existe), reportar cuales
            if "ForeignKeyViolation" in err or "foreign key" in err.lower():
                print(f"\n[ERROR] FK violation: algun usuario_id del seed no existe en `usuarios`.")
                print("         Esto pasa si el sync AD aun no corrio. Solucion:")
                print("         1) docker exec sgd-qas-backend python scripts/sync_ad_oficial.py")
                print("         2) Re-correr este seed.")
            else:
                print(f"\n[ERROR] {err[:500]}")
            print("         Rollback aplicado. BD sin cambios.")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
