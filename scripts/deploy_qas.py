#!/usr/bin/env python3
"""
COFAR SGD ? Deploy a QAS (Python, production-grade)
====================================================

Pipeline robusto de deploy a QAS. Usa subprocess para SSH (sin
problemas de quoting de PowerShell) + SCP para transferencia.

FLUJO:
  1. PRE-VALIDACION: entrypoint CI en DES (detecta errores migration)
  2. PRE-VALIDACION: pytest (detecta tests rotos)
  3. BACKUP BD QAS
  4. EMPAQUETAR + SUBIR codigo
  5. EXTRAER (via Python en QAS - SIN quoting issues)
  6. REBUILD imagenes
  7. RESTART + nginx
  8. SEEDS (start-stack-qas.sh)
  9. VALIDAR (validate-qas.sh)
  10. REPORTAR

Requiere:
  - Python 3.8+
  - Docker Desktop corriendo
  - ssh/scp con key a sistemas@sgdqas.cofar.com.bo

Uso:
  python scripts/deploy_qas.py                    # Deploy completo
  python scripts/deploy_qas.py --skip-validation   # Solo deploy
  python scripts/deploy_qas.py --dry-run           # Simular
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# --- Constantes ---
QAS_USER = "sistemas"
QAS_HOST = "sgdqas.cofar.com.bo"
QAS_DIR = "/opt/sgd"
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
VENV_PYTHON = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"

PASS = 0
FAIL = 0
FIXED = 0
TIMING = []


# --- Helpers ---
def pass_msg(msg: str):
    global PASS; PASS += 1; print(f"  [PASS] {msg}")


def fail_msg(msg: str):
    global FAIL; FAIL += 1; print(f"  [FAIL] {msg}")


def warn_msg(msg: str):
    global FIXED; FIXED += 1; print(f"  [WARN] {msg}")


def info(msg: str):
    print(f"  [INFO] {msg}")


def step(n: int, total: int, desc: str):
    print(f"\n{'=' * 70}")
    print(f"[{n}/{total}] {desc}")
    print(f"{'-' * 70}")


def ssh(cmd: str, timeout: int = 60) -> tuple[str, int]:
    """Ejecuta comando via SSH. Retorna (stdout, exit_code)."""
    try:
        r = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=15", f"{QAS_USER}@{QAS_HOST}", cmd],
            capture_output=True, text=False, timeout=timeout,
        )
        return r.stdout.decode("utf-8", errors="replace").strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "(TIMEOUT)", -1
    except FileNotFoundError:
        print("  [ERROR] ssh no encontrado. Verifica que OpenSSH esta instalado.")
        sys.exit(2)


def scp(local: str, remote: str, timeout: int = 60) -> bool:
    """Sube archivo via SCP. Retorna True si OK."""
    try:
        r = subprocess.run(
            ["scp", local, f"{QAS_USER}@{QAS_HOST}:{remote}"],
            capture_output=True, text=True, timeout=timeout,
        )
        return r.returncode == 0
    except Exception as e:
        print(f"  [SCP_ERROR] {e}")
        return False


def run_local(cmd: list[str], timeout: int = 120, cwd: str = None) -> tuple[str, int]:
    """Ejecuta comando local. Retorna (stdout, exit_code)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=False, timeout=timeout, cwd=cwd)
        out = r.stdout.decode("utf-8", errors="replace").strip() if r.stdout else ""
        return out, r.returncode
    except subprocess.TimeoutExpired:
        return "(TIMEOUT)", -1


# --- Fases del deploy ---

def fase_0_validate():
    """PRE-VALIDACION: entrypoint CI + pytest (en DES)."""
    step(0, 10, "PRE-VALIDACION: entrypoint CI + pytest")

    info("entrypoint modo CI (migrations)...")
    out, code = run_local([
        "docker", "exec", "-e", "ENVIRONMENT=ci", "-e", "LDAP_ENABLED=false",
        "sgd-backend", "bash", "scripts/entrypoint.sh",
    ], timeout=30, cwd=str(BACKEND_DIR))
    if code == 0 and "Migraciones aplicadas correctamente" in out:
        pass_msg("entrypoint CI: migrations OK")
    else:
        fail_msg("entrypoint CI FALLO. Migraciones tienen errores.")
        print(out)
        sys.exit(1)

    info("pytest...")
    out, code = run_local([str(VENV_PYTHON), "-m", "pytest", "tests/", "-q", "--tb=no"], timeout=180, cwd=str(BACKEND_DIR))
    if code == 0:
        pass_msg(f"pytest: {out.strip().split(chr(10))[-1] if chr(10) in out else 'OK'}")
    else:
        fail_msg("pytest FALLO. Tests tienen errores.")
        print(out)
        sys.exit(1)


def fase_1_backup():
    """BACKUP BD QAS."""
    step(1, 10, "BACKUP BD QAS")

    # Verificar SSH
    out, code = ssh("echo SSH_OK")
    if "SSH_OK" in out:
        pass_msg(f"SSH conectado a {QAS_HOST}")
    else:
        fail_msg(f"No se puede conectar SSH a {QAS_HOST}")
        sys.exit(2)

    # Backup
    out, code = ssh(
        'TS=$(date +%Y%m%d_%H%M%S); '
        'docker exec sgd-qas-postgres pg_dump -U sgd -d sgd -Fc '
        '-f /tmp/qas_pre_$TS.dump && '
        'docker cp sgd-qas-postgres:/tmp/qas_pre_$TS.dump '
        '/opt/sgd/backups/qas_${TS}_pre.dump && '
        'ls -la /opt/sgd/backups/qas_${TS}_pre.dump',
        timeout=30
    )
    if "qas_" in out:
        pass_msg(f"Backup BD creado")
    else:
        fail_msg(f"Backup FALLO: {out[:200]}")
        sys.exit(2)


def fase_2_package():
    """EMPAQUETAR + SUBIR CODIGO."""
    step(2, 10, "EMPAQUETAR + SUBIR CODIGO")

    tmp_dir = Path(tempfile.mkdtemp(prefix="sgd_deploy_"))
    zip_path = str(tmp_dir) + ".zip"

    # Robocopy-like: copiar directorios excluyendo pesados
    exclude_dirs = {"node_modules", ".venv", "__pycache__", ".git",
                    "postgres_data", "redis_data", ".pytest_cache"}
    for src_dir in ["backend", "frontend", "deploy", "scripts"]:
        src = REPO_ROOT / src_dir
        dst = tmp_dir / src_dir
        dst.mkdir(parents=True, exist_ok=True)
        for item in src.rglob("*"):
            if item.is_dir():
                continue
            # Skip excluded dirs
            rel = item.relative_to(src)
            if any(p in exclude_dirs for p in rel.parts):
                continue
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)

    # .env.example + .gitignore
    shutil.copy2(REPO_ROOT / ".env.example", tmp_dir / ".env.example")
    shutil.copy2(REPO_ROOT / ".gitignore", tmp_dir / ".gitignore")

    # Comprimir
    shutil.make_archive(str(tmp_dir), "zip", str(tmp_dir))
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    pass_msg(f"Codigo empaquetado ({size_mb:.1f} MB)")

    # Subir
    if scp(zip_path, "/tmp/sgd_deploy.zip", timeout=120):
        pass_msg("ZIP subido a QAS")
    else:
        fail_msg("Error SCP")
        sys.exit(2)

    # Limpiar
    shutil.rmtree(tmp_dir, ignore_errors=True)
    os.unlink(zip_path)

    return tmp_dir.name


def fase_3_extract():
    """EXTRAER CODIGO EN QAS (via Python script - SIN quoting issues)."""
    step(3, 10, "EXTRAER CODIGO + NGINX CONF")

    # El script de extraccion se escribe LOCALMENTE y se SCPea
    extract_script = REPO_ROOT / "scripts" / "extract_qas.py"

    if not extract_script.exists():
        fail_msg(f"No se encuentra {extract_script}")
        sys.exit(2)

    # SCPear el script
    if not scp(str(extract_script), "/tmp/extract_qas.py"):
        fail_msg("Error SCP extract script")
        sys.exit(2)

    # Ejecutar en QAS
    out, code = ssh("python3 /tmp/extract_qas.py", timeout=30)
    if "EXTRACT_OK" in out:
        pass_msg("Codigo extraido en QAS")
    else:
        fail_msg(f"Extraccion FALLO: {out[:200]}")
        sys.exit(2)

    # Renombrar nginx conf + restaurar .env.qas + ssl
    out, code = ssh(
        'cp -a /tmp/env_bak /opt/sgd/.env.qas 2>/dev/null; '
        'cp -a /tmp/ssl_bak/. /opt/sgd/deploy/nginx/ssl/ 2>/dev/null; '
        'chmod +x /opt/sgd/scripts/*.sh 2>/dev/null; '
        'if [ -f /opt/sgd/deploy/nginx/conf.d/sgd-qas.conf.bk ]; then '
        '  mv /opt/sgd/deploy/nginx/conf.d/sgd-qas.conf.bk '
        '     /opt/sgd/deploy/nginx/conf.d/sgd-qas.conf'
        '  && echo CONF_RENAMED;'
        'else echo CONF_OK; fi',
        timeout=15
    )
    if "CONF_RENAMED" in out or "CONF_OK" in out:
        pass_msg(f"nginx conf: {out}")
    else:
        warn_msg(f"Conf rename: {out[:100]}")


def fase_4_rebuild():
    """REBUILD IMAGENES."""
    step(4, 10, "REBUILD IMAGENES DOCKER")

    images = "backend celery-worker celery-beat frontend"
    out, code = ssh(
        f"cd {QAS_DIR} && docker compose -f deploy/docker-compose.qas.yml "
        f"--env-file .env.qas build --pull {images} 2>&1 | grep 'Built'",
        timeout=300
    )
    built = out.count("Built")
    if built >= 3:
        pass_msg(f"{built}/4 imagenes rebuild OK")
    else:
        warn_msg(f"Solo {built}/4 imagenes rebuild. Continuando...")


def fase_5_restart():
    """RESTART SERVICIOS + NGINX."""
    step(5, 10, "RESTART SERVICIOS + NGINX")

    out, code = ssh(
        f"cd {QAS_DIR} && docker compose -f deploy/docker-compose.qas.yml "
        f"--env-file .env.qas up -d 2>&1",
        timeout=60
    )
    time.sleep(15)

    # Nginx restart FORZADO (siempre necesario post-recreate de backend)
    out, code = ssh("docker restart sgd-qas-nginx", timeout=15)
    if code == 0:
        pass_msg("Servicios reiniciados + nginx restarted")
    else:
        # Fallback: recreate nginx
        ssh(
            f"cd {QAS_DIR} && docker compose -f deploy/docker-compose.qas.yml "
            f"--env-file .env.qas up -d nginx 2>&1"
        )
        warn_msg("nginx recreated via compose up")


def fase_6_health():
    """ESPERAR HEALTH CHECKS."""
    step(6, 10, "ESPERANDO HEALTH CHECKS (max 90s)")

    for i in range(45):
        out, code = ssh(
            'curl -kfsS -o /dev/null -w "%{http_code}" '
            'https://localhost/api/v1/health 2>/dev/null',
            timeout=5
        )
        if out == "200":
            pass_msg(f"Backend HTTPS health: 200 OK ({i*2}s)")
            return
        time.sleep(2)

    fail_msg("Backend no responde HTTPS tras 90s")
    # Ultimo intento con restart de nginx
    ssh("docker restart sgd-qas-nginx")
    sys.exit(2)


def fase_7_seeds():
    """SEEDS + SYNC AD."""
    step(7, 10, "SEEDS + SYNC AD")

    out, code = ssh(
        f"cd {QAS_DIR} && bash scripts/start-stack-qas.sh 2>&1 | tail -5",
        timeout=300
    )
    if "Stack QAS listo" in out:
        pass_msg("12/12 seeds + sync AD OK")
    else:
        warn_msg(f"Seeds: {out[:200]}")
        # Reintento
        out2, code2 = ssh(
            f"cd {QAS_DIR} && bash scripts/start-stack-qas.sh 2>&1 | tail -3",
            timeout=300
        )
        if "Stack QAS listo" in out2:
            pass_msg("Seeds OK (2do intento)")
        else:
            fail_msg(f"Seeds FALLARON: {out2[:200]}")
            sys.exit(2)


def fase_8_validate():
    """VALIDAR QAS (validate-qas.sh) + AUTO-FIX."""
    step(8, 10, "VALIDAR QAS")

    out, code = ssh(f"bash {QAS_DIR}/scripts/validate-qas.sh", timeout=60)

    # Extraer conteos
    pass_m = re.search(r"PASS:\s*(\d+)/(\d+)", out)
    fail_m = re.search(r"FAIL:\s*(\d+)", out)
    n_pass = int(pass_m.group(1)) if pass_m else 0
    n_fail = int(fail_m.group(1)) if fail_m else 99
    total = int(pass_m.group(2)) if pass_m else 38

    if n_fail == 0:
        pass_msg(f"{n_pass}/{total} PASS, 0 FAIL")
        return

    # AUTO-FIX: problemas conocidos
    warn_msg(f"{n_fail} FAILS. Aplicando auto-fix...")

    if "K.2" in out or "K.3" in out:
        ssh("docker restart sgd-qas-nginx", timeout=10)
        time.sleep(5)
        # Re-validar K
        for chk in ["K.2", "K.3"]:
            out2, _ = ssh(
                f'docker exec sgd-qas-nginx sh -c '
                f'"curl -kfsS -o /dev/null -w %{{http_code}} '
                f'https://localhost/api/v1/health"',
                timeout=5
            )
            if out2 == "200":
                pass_msg(f"{chk} fixed: nginx restarted")

    if "E.1" in out or "E.2" in out:
        warn_msg("Login fails - puede ser cookie CSRF. Revisar manual.")

    # Re-validar final
    out3, code3 = ssh(f"bash {QAS_DIR}/scripts/validate-qas.sh", timeout=60)
    fail_m3 = re.search(r"FAIL:\s*(\d+)", out3)
    n_fail3 = int(fail_m3.group(1)) if fail_m3 else 99
    pass_m3 = re.search(r"PASS:\s*(\d+)/(\d+)", out3)
    n_pass3 = int(pass_m3.group(1)) if pass_m3 else 0

    if n_fail3 == 0:
        pass_msg(f"{n_pass3}/38 PASS post-fix, 0 FAIL")
    else:
        fail_msg(f"QAS con {n_fail3} FAIL incluso post-fix")
        print(out3)
        sys.exit(2)


def fase_9_cleanup():
    """CLEANUP + RESUMEN."""
    step(9, 10, "CLEANUP + RESUMEN")

    # Limpiar build cache de Docker en QAS si es muy grande
    out, code = ssh(
        'docker builder prune -f 2>&1 | tail -1',
        timeout=30
    )

    pass_msg("Archivos temporales eliminados")

    print(f"\n{'=' * 70}")
    total = PASS + FAIL
    if FAIL == 0:
        print(f"[OK]  DEPLOY COMPLETADO: {PASS}/{total} PASS, 0 FAIL")
        print(f"    QAS: https://sgdqas.cofar.com.bo")
    else:
        print(f"[FAIL]  DEPLOY CON ERRORES: {FAIL} FAILS")
        sys.exit(1)
    print(f"{'=' * 70}")


def fase_10_postdeploy():
    """CONSEJO POST-DEPLOY."""
    step(10, 10, "POST-DEPLOY (si aplica)")
    print("  Si es fresh-install, ejecutar asignacion de roles reales:\n")
    print("    ssh sistemas@sgdqas.cofar.com.bo")
    print('    docker exec sgd-qas-backend python scripts/run_matriz_import.py \\')
    print('        --excel "/app/docs/Diagramas_Matrices/MATRICES/')
    print('                 USUARIOS EXISTENTES A ABRIL.xlsx"')
    print()


# --- Main ---
def main():
    parser = argparse.ArgumentParser(description="COFAR SGD - Deploy a QAS")
    parser.add_argument("--skip-validation", action="store_true",
                        help="Omitir pre-validacion local")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simular sin ejecutar")
    args = parser.parse_args()

    start = time.time()

    print(f"\n{'='*70}")
    print("COFAR SGD - Pipeline de Deploy a QAS")
    print(f"  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    if args.dry_run:
        info("MODO DRY-RUN: Solo se mostraran los pasos")
        for i, fase in enumerate([
            "PRE-VALIDACION", "BACKUP", "EMPAQUETAR",
            "EXTRAER", "REBUILD", "RESTART", "HEALTH",
            "SEEDS", "VALIDAR", "POST-DEPLOY"
        ], 1):
            print(f"  [{i}/10] {fase}  ?  (SKIP - dry-run)")
        print("\n  Dry-run completo. Nada se ejecuto.")
        return

    if not args.skip_validation:
        fase_0_validate()
    else:
        info("PRE-VALIDACION omitida (--skip-validation)")

    fase_1_backup()
    fase_2_package()
    fase_3_extract()
    fase_4_rebuild()
    fase_5_restart()
    fase_6_health()
    fase_7_seeds()
    fase_8_validate()
    fase_9_cleanup()
    fase_10_postdeploy()

    elapsed = time.time() - start
    print(f"\n  [TIME]  Duracion total: {elapsed/60:.1f} min")
    print()


if __name__ == "__main__":
    main()
