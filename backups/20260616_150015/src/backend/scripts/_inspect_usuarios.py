"""
INVENTARIO DE USUARIOS - solo lectura, NO modifica nada.
Para correr antes de la limpieza de BD. Muestra quienes estan
hoy y contra que lista de 10 'base' se va a comparar.

Uso:
    .\\.venv\\Scripts\\python.exe scripts\\_inspect_usuarios.py
"""
import sys
import asyncio
from pathlib import Path

# Cargar .env raiz (igual que el backend)
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


# Los 10 usernames que TIENEN que quedar
USERNAMES_BASE = {
    # 4 de seed_data.py
    "aromero", "solicitante", "admin", "visualizador",
    # 5 de seed_local_test_users.py
    "admin_local", "eto_test", "elaborador_revisor",
    "elaborador_revisor_aprobador", "visualizador_cl",
    # 1 de LDAP (vos)
    "ychavez",
}


async def main():
    conn = await asyncpg.connect(DATABASE_URL_SYNC)
    try:
        # Contar total
        total = await conn.fetchval("SELECT COUNT(*) FROM usuarios")
        print(f"\n=== TOTAL USUARIOS EN BD: {total} ===\n")

        # Listar TODOS los usuarios
        rows = await conn.fetch("""
            SELECT id, username, nombre_completo, email, cargo,
                   area_id, estado, ausente, ad_postal_code,
                   azure_oid IS NOT NULL AS es_del_ad,
                   ad_last_synced_at IS NOT NULL AS fue_sincronizado
            FROM usuarios
            ORDER BY id
        """)

        print(f"{'id':>4}  {'username':<35}  {'area':>4}  {'estado':<8}  {'ad':>2}  {'sap':<6}  nombre")
        print("-" * 130)

        base_ok = []
        sobran = []
        for r in rows:
            uid = r["id"]
            username = r["username"]
            area = r["area_id"] if r["area_id"] is not None else "-"
            estado = r["estado"]
            es_ad = "SI" if r["es_del_ad"] else "no"
            sap = (r["ad_postal_code"] or "")[:6] if r["ad_postal_code"] else "-"
            nombre = (r["nombre_completo"] or "")[:40]
            print(f"{uid:>4}  {username:<35}  {area:>4}  {estado:<8}  {es_ad:>2}  {sap:<6}  {nombre}")
            if username in USERNAMES_BASE:
                base_ok.append(username)
            else:
                sobran.append(username)

        print()
        print("=" * 70)
        print(f"Usuarios BASE que SI estan en BD: {len(base_ok)}/10")
        if len(base_ok) < 10:
            faltan = USERNAMES_BASE - set(base_ok)
            print(f"  FALTAN ({len(faltan)}): {sorted(faltan)}")
        else:
            print("  OK los 10 estan.")

        print()
        print(f"Usuarios a BORRAR (no son los 10 base): {len(sobran)}")
        if sobran:
            print(f"  Primeros 10: {sobran[:10]}")
            if len(sobran) > 10:
                print(f"  ... y {len(sobran) - 10} mas")

        # Verificar dependencias (FKs) que puedan impedir el delete
        print()
        print("=" * 70)
        print("Chequeo FKs que podrian bloquear el DELETE:")
        for fk_table in ["usuario_roles", "usuario_modulos", "delegaciones",
                         "ausencias", "firma_digital", "log_sync_ad"]:
            try:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {fk_table}")
                print(f"  {fk_table}: {count} registros (se borraran en cascada o habra que limpiar antes)")
            except asyncpg.UndefinedTableError:
                print(f"  {fk_table}: tabla no existe (no aplica)")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
