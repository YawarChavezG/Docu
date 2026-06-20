"""
Generate seed_usuario_roles.sql with portable INSERTs (using username + codigo_rol).
"""
import subprocess
import sys
from pathlib import Path

DOCKER_CMD = ["docker", "exec", "sgd-postgres", "psql", "-U", "sgd", "-d", "sgd", "-tA"]
OUT = Path("C:/Users/ychavez/PROYECTOS-DOCKER/SGD-DES/backend/scripts/seed_usuario_roles.sql")


def main() -> None:
    # Extract (username, codigo) pairs from DES, escaped for SQL.
    # PostgreSQL uses $$ ... $$ as dollar-quoting for string literals.
    # Inside $$...$$, a literal $ is doubled: $$foo bar$$ contains 'foo bar'.
    # But our usernames/role codes never contain $, so no escaping needed.
    # NOTE: use raw string r'...' to prevent Python from interpreting \$.
    sql = (
        r"SELECT '($$' || u.username || '$$, $$' || r.codigo || '$$)' "
        "FROM usuario_roles ur "
        "JOIN usuarios u ON u.id = ur.usuario_id "
        "JOIN roles r ON r.id = ur.rol_id "
        "ORDER BY u.username, r.codigo;"
    )
    res = subprocess.run(
        DOCKER_CMD + ["-c", sql], capture_output=True, text=True, check=True
    )
    pairs = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
    if not pairs:
        print("ERROR: no pairs found", file=sys.stderr)
        sys.exit(1)

    # Build a single INSERT ... SELECT ... JOIN with VALUES clause.
    # pairs is a list of strings like "($$aadriazola$$, $$VISUALIZADOR (CL-EVAL)$$)"
    # Explicit ::text cast on VALUES columns so the JOIN has matching types.
    # roles.codigo is type `codigo_rol` (a PostgreSQL enum), so we cast
    # the literal to ::text and let the JOIN compare text-to-enum.
    values_sql = ",\n    ".join(pairs)
    full_sql = (
        "-- Sesion 33 (deploy v1.1.0-qas): snapshot de las 729 asignaciones\n"
        "-- usuario_roles de DES, portado via (username, codigo_rol) para que\n"
        "-- funcione en cualquier ambiente donde existan esos usuarios + roles.\n"
        "--\n"
        "-- Idempotente: ON CONFLICT (usuario_id, rol_id) DO NOTHING sobre la PK.\n"
        "-- Si un usuario o rol no existe, la fila se ignora silenciosamente.\n"
        f"-- Generado: {len(pairs)} asignaciones.\n"
        "\n"
        "INSERT INTO usuario_roles (usuario_id, rol_id)\n"
        "SELECT u.id, r.id\n"
        "FROM (VALUES\n"
        f"    {values_sql}\n"
        ") AS v(username, codigo)\n"
        "JOIN usuarios u ON u.username = v.username\n"
        "JOIN roles r ON r.codigo::text = v.codigo\n"
        "ON CONFLICT (usuario_id, rol_id) DO NOTHING;\n"
    )
    # Write without BOM (Windows-safe; python's default utf-8 has no BOM).
    OUT.write_text(full_sql, encoding="utf-8")
    print(f"OK: wrote {len(pairs)} pairs to {OUT}")
    print(f"Size: {OUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()
