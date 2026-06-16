"""
SCRIPT OFICIAL de sincronizacion de usuarios desde el AD de COFAR.

Es la fuente de verdad para el flujo de sync AD. Genera el CSV
`usuarios_sap_FINAL2026.csv` (~753 usuarios) que sera la base para
alimentar el endpoint POST /api/v1/usuarios/sync-ad del backend.

Logica (replica el flujo n8n de COFAR):
  1. Query LDAP con filtro (&(objectClass=user)(sAMAccountType=805306368))
     en OU=Oficina Central,DC=cofar,DC=com
  2. Excluir OU=especiales / OU=pruebas
  3. Excluir cuentas deshabilitadas (bit 1 = ACCOUNTDISABLE en userAccountControl).
     Chequeamos el BIT 1 con `(uac & 2) != 0`, no valores literales como
     "514" o "66050" -- en el AD de COFAR hay cuentas deshabilitadas con
     uAC 4098, 8194, etc. que pasaban sin filtrar.
  4. Excluir sam = dlanchipa / ozegarra
  5. Excluir usuarios sin codigo SAP (postalCode vacio)

Uso:
    .\\.venv\\Scripts\\python.exe scripts\\sync_ad_oficial.py

Output: scripts/usuarios_sap_FINAL2026.csv (753 filas esperado)

NOTA: este script es la version validada de test5_final_745.py.
NO comparar uac contra una lista hardcodeada; usar siempre bit-mask.
"""
import sys
import csv
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
env_path = REPO_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)

from ldap3 import Connection
from app.core.config import settings
from app.services.ad_service import build_server

# CORRECCIÓN CRÍTICA: Se añade "userAccountControl" a la lista para que el AD lo devuelva
ATRIBUTOS = [
    "sn", "title", "physicalDeliveryOfficeName", "telephoneNumber",
    "givenName", "department", "sAMAccountName", "mobile", "postalCode",
    "mail", "company", "info", "userAccountControl"
]

def _primero(valor):
    """Aplana el valor de un atributo ldap3 a string plano o entero según corresponda."""
    if valor is None:
        return ""
    if isinstance(valor, list):
        if not valor:
            return ""
        v = valor[0]
    else:
        v = valor
    if isinstance(v, (bytes, bytearray)):
        return v.decode("utf-8", errors="ignore").strip()
    return str(v).strip()


def _es_cuenta_deshabilitada(uac_raw) -> bool:
    """
    Devuelve True si la cuenta esta deshabilitada.
    Filtra explícitamente por operaciones de bits (bit 1 / valor 2 es ACCOUNTDISABLE).
    Esto capturará automáticamente 514, 66050, 4098 y cualquier otra variante deshabilitada.
    """
    s = _primero(uac_raw)
    if not s:
        return False
    try:
        # El bit 1 (valor 2) indica cuenta deshabilitada en Active Directory
        return (int(s) & 2) != 0
    except (ValueError, TypeError):
        return False


server = build_server()
conn = Connection(
    server, user=settings.ldap_bind_user, password=settings.ldap_bind_password,
    auto_bind=True, read_only=True, receive_timeout=30,
)
print(f"Bind OK como {settings.ldap_bind_user}")
print()

# ─── PASO 1: Query LDAP estilo n8n ───
print("=" * 70)
print("PASO 1: Query LDAP estilo n8n")
print("=" * 70)
conn.search(
    search_base="ou=Oficina Central,dc=cofar,dc=com",
    search_filter="(&(objectClass=user)(sAMAccountType=805306368))",
    search_scope="SUBTREE",
    attributes=ATRIBUTOS,
    size_limit=5000,
)
total_paso1 = len(conn.entries)
print(f"   Entries del AD: {total_paso1}")
print()

# ─── PASO 2: Filtros del JS de n8n ───
print("=" * 70)
print("PASO 2: Filtros del JS de n8n")
print("=" * 70)

items = []
excl_por_ou = 0
excl_por_uac = 0
excl_por_sam = 0
debug_uac_examples = []

for entry in conn.entries:
    attrs = entry.entry_attributes_as_dict
    sam = _primero(attrs.get("sAMAccountName"))
    if not sam:
        continue

    # Filtro 1: OU=especiales o OU=pruebas
    dn_lower = str(entry.entry_dn).lower()
    if "ou=especiales" in dn_lower or "ou=pruebas" in dn_lower:
        excl_por_ou += 1
        continue

    # Filtro 2: cuenta deshabilitada
    uac_raw = attrs.get("userAccountControl")
    uac_flat = _primero(uac_raw)
    deshabilitada = _es_cuenta_deshabilitada(uac_raw)

    if deshabilitada and len(debug_uac_examples) < 5:
        debug_uac_examples.append({
            "sam": sam,
            "uac_raw": repr(uac_raw),
            "uac_flat": repr(uac_flat),
            "type": type(uac_raw).__name__,
        })

    if deshabilitada:
        excl_por_uac += 1
        continue

    # Filtro 3: sam especifico
    if sam.lower() in ("dlanchipa", "ozegarra"):
        excl_por_sam += 1
        continue

    items.append({
        "dn": str(entry.entry_dn),
        "sn": _primero(attrs.get("sn")),
        "title": _primero(attrs.get("title")),
        "physicalDeliveryOfficeName": _primero(attrs.get("physicalDeliveryOfficeName")),
        "telephoneNumber": _primero(attrs.get("telephoneNumber")),
        "givenName": _primero(attrs.get("givenName")),
        "department": _primero(attrs.get("department")),
        "sAMAccountName": sam,
        "mobile": _primero(attrs.get("mobile")),
        "postalCode": _primero(attrs.get("postalCode")),
        "mail": _primero(attrs.get("mail")),
        "company": _primero(attrs.get("company")),
        "info": _primero(attrs.get("info")),
        "userAccountControl": uac_flat,
    })

# Mostrar debug de uAC si encontramos deshabilitados
if debug_uac_examples:
    print("   DEBUG: Ejemplos de cuentas deshabilitadas (para entender el formato):")
    for ex in debug_uac_examples:
        print(f"      sam={ex['sam']:25s}  uAC raw type={ex['type']:10s}  raw={ex['uac_raw']:20s}  flat={ex['uac_flat']:20s}")
else:
    print("   DEBUG: NO se detectaron cuentas deshabilitadas. Eso es raro.")
    from collections import Counter
    uac_counter = Counter()
    for entry in conn.entries:
        attrs = entry.entry_attributes_as_dict
        uac_raw = attrs.get("userAccountControl")
        uac_flat = _primero(uac_raw)
        uac_counter[uac_flat] += 1
    print(f"   Distribucion de uAC encontrados: {dict(uac_counter.most_common(20))}")
print()

print(f"   Excluidos por OU (Especiales/Pruebas):   {excl_por_ou}")
print(f"   Excluidos por uAC (deshabilitados, bit 1): {excl_por_uac}")
print(f"   Excluidos por sam (dlanchipa/ozegarra):    {excl_por_sam}")
print(f"   --> QUEDAN: {len(items)}")
print()

# ─── PASO 3: Filtro postalCode ───
print("=" * 70)
print("PASO 3: Filtro postalCode (codigo SAP)")
print("=" * 70)
items_con_sap = [u for u in items if u["postalCode"]]
items_sin_sap = [u for u in items if not u["postalCode"]]
print(f"   Con codigo SAP:    {len(items_con_sap)}")
print(f"   Sin codigo SAP:    {len(items_sin_sap)}")
print()

# Distribucion por OU
ou_dist = {}
for u in items_con_sap:
    for p in u["dn"].split(","):
        if p.strip().lower().startswith("ou="):
            ou = p.strip()[3:]
            ou_dist[ou] = ou_dist.get(ou, 0) + 1
            break

print("=" * 70)
print("DISTRIBUCION POR OU (del resultado final):")
print("=" * 70)
for ou, count in sorted(ou_dist.items(), key=lambda x: -x[1]):
    print(f"   {count:4d}  OU={ou}")
print()

# ─── EXPORTAR A CSV ───
csv_cols = [
    "dn", "sn", "title", "physicalDeliveryOfficeName", "telephoneNumber",
    "givenName", "department", "sAMAccountName", "mobile", "postalCode",
    "mail", "company", "info", "userAccountControl",
]
# Output path: configurable via env var, default /app/storage/ (writable por sgduser
# en QAS donde /app/scripts/ es propiedad de root via bind mount).
# Si se quiere el path legacy, set SYNC_AD_OUTPUT_DIR=/app/scripts/.
out_dir = Path(os.environ.get("SYNC_AD_OUTPUT_DIR", "/app/storage"))
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "usuarios_sap_FINAL2026.csv"
with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=csv_cols, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    for u in items_con_sap:
        row = {k: u.get(k, "") for k in csv_cols}
        writer.writerow(row)

print("=" * 70)
print(f"ARCHIVO EXPORTADO: {out_path}  ({len(items_con_sap)} filas)")
print()
print("=" * 70)
print("CONCLUSION")
print("=" * 70)
print(f"""
Total flow:
  - LDAP query (Paso 1):     {total_paso1}   entries
  - Filtros n8n (Paso 2):    {len(items)}   usuarios
  - Filtro postal (Paso 3):  {len(items_con_sap)}   usuarios
""")