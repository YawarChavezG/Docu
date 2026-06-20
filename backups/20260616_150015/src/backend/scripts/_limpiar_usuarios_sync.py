"""
LIMPIEZA DE USUARIOS TRAIDOS POR SYNC AD ANTERIOR.

Borra todos los usuarios de la BD EXCEPTO los 10 base:
  - 4 de seed_data.py:           aromero, solicitante, admin, visualizador
  - 5 de seed_local_test_users:  admin_local, eto_test, elaborador_revisor,
                                 elaborador_revisor_aprobador, visualizador_cl
  - 1 LDAP real (vos):           ychavez

Es seguro: las FKs de usuario_roles y usuario_modulos tienen
ondelete=CASCADE, asi que el DELETE borra los vinculos automaticamente.

Uso:
    .\\.venv\\Scripts\\python.exe scripts\\_limpiar_usuarios_sync.py

NO pedir confirmacion: ya validaste la lista de 10 base.
"""
import sys
import asyncio
from pathlib import Path

from dotenv import load_dotenv
import os

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO_ROOT / ".env", override=True)

POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_DB = os.environ["POSTGRES_DB"]
HOST_PORT_POSTGRES = os.environ.get("HOST_PORT_POSTGRES", "25432")
DATABASE_URL_SYNC = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@127.0.0.1:{HOST_PORT_POSTGRES}/{POSTGRES_DB}"

import asyncpg


USERNAMES_BASE = [
    "aromero", "solicitante", "admin", "visualizador",  # seed_data
    "admin_local", "eto_test", "elaborador_revisor",  # seed_local
    "elaborador_revisor_aprobador", "visualizador_cl",
    "ychavez",  # LDAP real
]


async def main():
    conn = await asyncpg.connect(DATABASE_URL_SYNC)
    try:
        total_antes = await conn.fetchval("SELECT COUNT(*) FROM usuarios")
        print(f"Usuarios ANTES: {total_antes}")

        # Borrar todo lo que no este en la lista base
        # Postgres: usar ANY($1::text[]) para el IN
        result = await conn.execute("""
            DELETE FROM usuarios
            WHERE username <> ALL($1::text[])
        """, USERNAMES_BASE)
        # result viene como 'DELETE 517' (cantidad afectada)
        print(f"Borrados: {result}")

        total_despues = await conn.fetchval("SELECT COUNT(*) FROM usuarios")
        print(f"Usuarios DESPUES: {total_despues}")

        print()
        print("=" * 60)
        print(f"Usuarios que quedaron (esperados: {len(USERNAMES_BASE)}):")
        print("=" * 60)
        rows = await conn.fetch("""
            SELECT id, username, nombre_completo, cargo, estado
            FROM usuarios
            ORDER BY id
        """)
        for r in rows:
            print(f"  [{r['id']:>3}] {r['username']:<35} {r['nombre_completo'][:30]:<30} ({r['estado']})")

        # Validar contra la lista esperada
        usernames_en_bd = {r["username"] for r in rows}
        esperados = set(USERNAMES_BASE)
        if usernames_en_bd == esperados:
            print()
            print("OK: los usernames en BD coinciden exactamente con los 10 base.")
        else:
            faltan = esperados - usernames_en_bd
            sobran = usernames_en_bd - esperados
            if faltan: print(f"FALTAN: {sorted(faltan)}")
            if sobran: print(f"SOBRAN: {sorted(sobran)}")
            sys.exit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
