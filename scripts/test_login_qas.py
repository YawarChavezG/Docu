"""Test login en QAS."""
import json
import subprocess
import sys

cmd = (
    'curl -kfsS -X POST https://localhost/api/v1/login '
    '-H "Content-Type: application/json" '
    '-d \'{"username":"aromero","password":"cofar.2026","auth_source":"local"}\''
)

r = subprocess.run(
    ["ssh", "sistemas@sgdqas.cofar.com.bo", cmd],
    capture_output=True, text=False, timeout=15,
)
out = r.stdout.decode("utf-8", errors="replace").strip()
print(f"Exit code: {r.returncode}")
if r.returncode == 0 and out:
    d = json.loads(out)
    u = d.get("usuario", {})
    print(f"Login: OK")
    print(f"  Usuario: {u.get('username', '?')}")
    print(f"  Cargo: {u.get('cargo', '?')}")
    print(f"  Roles: {[x.get('codigo') for x in u.get('roles', [])]}")
else:
    print(f"Respuesta: {out[:500]}")
