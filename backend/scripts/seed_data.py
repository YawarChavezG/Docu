"""
Seed data — COFAR SGD

Siembra catalogos iniciales:
- 5 roles
- 10 módulos
- 10 gerencias (8 con áreas + 2 sin detalle)
- ~25 áreas
- 4 usuarios stub de desarrollo

Uso:
  docker exec sgd-backend python scripts/seed_data.py

Idempotente: si los datos ya existen, los actualiza en vez de duplicar.
"""
import asyncio
import sys
from pathlib import Path

# Make 'app' importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.rol import Rol, CodigoRol
from app.models.modulo import Modulo, CodigoModulo
from app.models.gerencia import Gerencia
from app.models.area import Area
from app.models.usuario import Usuario, EstadoUsuario, EstadoDelegacion


# ─── Datos a sembrar ───

ROLES_DATA = [
    {
        "codigo": CodigoRol.ADMIN,
        "nombre": "Administrador del Sistema",
        "descripcion": "Configuración técnica y parametrización global. Acceso total.",
        "requiere_delegado": False,
    },
    {
        "codigo": CodigoRol.ETO,
        "nombre": "Gestor Documental ETO",
        "descripcion": "Liberación, obsolescencia, parametrización operativa, generación de copias.",
        "requiere_delegado": True,
    },
    {
        "codigo": CodigoRol.ELABORADOR_REVISOR,
        "nombre": "Elaborador - Revisor",
        "descripcion": "Crea solicitudes y revisa documentos. NO aprueba.",
        "requiere_delegado": True,
    },
    {
        "codigo": CodigoRol.ELABORADOR_REVISOR_APROBADOR,
        "nombre": "Elaborador - Revisor - Aprobador",
        "descripcion": "Crea, revisa y aprueba documentos. Acceso completo al flujo.",
        "requiere_delegado": True,
    },
    {
        "codigo": CodigoRol.VISUALIZADOR_CL_EVAL,
        "nombre": "Visualizador (Control de Lectura y Evaluación)",
        "descripcion": "Solo lectura, controles de lectura obligatorios y exámenes de capacitación.",
        "requiere_delegado": False,
    },
]

MODULOS_DATA = [
    {"codigo": CodigoModulo.BANDEJA_TAREAS, "nombre": "Bandeja de Tareas", "ruta_ui": "/bandeja", "orden": 1},
    {"codigo": CodigoModulo.MI_BANDEJA, "nombre": "Mi Bandeja", "ruta_ui": "/bandeja", "orden": 2},
    {"codigo": CodigoModulo.LISTA_MAESTRA, "nombre": "Lista Maestra", "ruta_ui": "/lista", "orden": 3},
    {"codigo": CodigoModulo.CONSULTAR_DOCUMENTOS, "nombre": "Consultar Documentos", "ruta_ui": "/consulta", "orden": 4},
    {"codigo": CodigoModulo.MIS_EVALUACIONES, "nombre": "Mis Evaluaciones", "ruta_ui": "/evaluaciones", "orden": 5},
    {"codigo": CodigoModulo.ASISTENTE_IA, "nombre": "Asistente IA", "ruta_ui": "/chat", "orden": 6},
    {"codigo": CodigoModulo.NUEVA_SOLICITUD, "nombre": "Nueva Solicitud", "ruta_ui": "/version-editable", "orden": 7},
    {"codigo": CodigoModulo.PLANTILLAS_DOCUMENTALES, "nombre": "Plantillas Documentales", "ruta_ui": "/plantillas", "orden": 8},
    {"codigo": CodigoModulo.PARAMETRIZACION, "nombre": "Parametrización General", "ruta_ui": "/parametrizacion", "orden": 9},
    {"codigo": CodigoModulo.REPORTES, "nombre": "Reportes", "ruta_ui": "/reportes", "orden": 10},
    {"codigo": CodigoModulo.TODOS, "nombre": "Todos los Módulos (Bypass)", "ruta_ui": None, "orden": 99},
]

GERENCIAS_DATA = [
    # (sigla, nombre, orden)
    ("CAL", "CALIDAD", 1),
    ("PLA", "PLANTA", 2),
    ("RRH", "RECURSOS HUMANOS", 3),
    ("ADM", "ADMINISTRACION", 4),
    ("COM", "COMERCIAL", 5),
    ("GEN", "GENERAL", 6),
    ("TER", "TERCIA", 7),
    ("LOG", "LOGISTICA", 8),
    ("OPS", "OPERACIONES", 9),
    ("AUD", "AUDITORIA INTERNA", 10),
]

AREAS_DATA = [
    # (gerencia_sigla, sigla_area, nombre_area, orden)
    # CALIDAD
    ("CAL", "CC", "CONTROL DE CALIDAD", 1),
    ("CAL", "DT", "DIRECCION TECNICA", 2),
    ("CAL", "EST", "ESTABILIDAD", 3),
    ("CAL", "GAC", "GARANTIA DE CALIDAD", 4),
    ("CAL", "MCB", "MICROBIOLOGIA", 5),
    ("CAL", "REG", "REGENCIA FARMACEUTICA", 6),
    ("CAL", "VAL", "VALIDACIONES", 7),
    ("CAL", "FV", "FARMACOVIGILANCIA", 8),
    ("CAL", "BEQ", "BIOEQUIVALENCIA", 9),
    ("CAL", "IDF", "INVESTIGACION Y DESARROLLO FARMACEUTICO", 10),
    ("CAL", "DEI", "DESARROLLO INDUSTRIAL", 11),
    # PLANTA
    ("PLA", "ACD", "ACONDICIONAMIENTO", 1),
    ("PLA", "BET", "BETALACTAMICOS", 2),
    ("PLA", "LE", "LIQUIDOS ESTERILES", 3),
    ("PLA", "LNE", "LIQUIDOS NO ESTERILES", 4),
    ("PLA", "SIMA", "SEGURIDAD INDUSTRIAL Y MEDIO AMBIENTE", 5),
    ("PLA", "SMS", "SEMISOLIDOS", 6),
    ("PLA", "SNE", "SOLIDOS NO ESTERILES", 7),
    ("PLA", "CB", "CAPSULAS BLANDAS", 8),
    ("PLA", "PRO", "PRODUCCION", 9),
    # RECURSOS HUMANOS
    ("RRH", "MLB", "MEDICINA LABORAL", 1),
    ("RRH", "TAL", "GESTION DE TALENTO HUMANO", 2),
    ("RRH", "ADM", "ADMINISTRACION", 3),
]

USUARIOS_STUB_DATA = [
    # Para DES (no se valida contra AD). QAS usara sync AD real.
    {
        "username": "aromero",
        "email": "aromero@cofar.local",
        "nombre_completo": "Aracely Romero",
        "iniciales": "AR",
        "cargo": "Gestor Documental ETO",
        "area_sigla": "CC",
        "rol": CodigoRol.ETO,
        "modulos": [CodigoModulo.TODOS],
        "estado_delegacion": EstadoDelegacion.NA,
    },
    {
        "username": "solicitante",
        "email": "solicitante@cofar.local",
        "nombre_completo": "Juan Perez",
        "iniciales": "JP",
        "cargo": "Analista de Calidad",
        "area_sigla": "CC",
        "rol": CodigoRol.ELABORADOR_REVISOR_APROBADOR,
        "modulos": [
            CodigoModulo.MI_BANDEJA, CodigoModulo.LISTA_MAESTRA,
            CodigoModulo.CONSULTAR_DOCUMENTOS, CodigoModulo.MIS_EVALUACIONES,
            CodigoModulo.NUEVA_SOLICITUD, CodigoModulo.PLANTILLAS_DOCUMENTALES,
            CodigoModulo.ASISTENTE_IA,
        ],
        "estado_delegacion": EstadoDelegacion.PENDIENTE,
    },
    {
        "username": "admin",
        "email": "admin@cofar.local",
        "nombre_completo": "Lucia Herrera",
        "iniciales": "LH",
        "cargo": "Administrador del Sistema",
        "area_sigla": None,
        "rol": CodigoRol.ADMIN,
        "modulos": [CodigoModulo.TODOS],
        "estado_delegacion": EstadoDelegacion.NA,
    },
    {
        "username": "visualizador",
        "email": "visualizador@cofar.local",
        "nombre_completo": "Diego Quispe",
        "iniciales": "DQ",
        "cargo": "Operario Planta Solidos",
        "area_sigla": "SNE",
        "rol": CodigoRol.VISUALIZADOR_CL_EVAL,
        "modulos": [
            CodigoModulo.BANDEJA_TAREAS, CodigoModulo.LISTA_MAESTRA,
            CodigoModulo.MIS_EVALUACIONES, CodigoModulo.ASISTENTE_IA,
        ],
        "estado_delegacion": EstadoDelegacion.NA,
    },
]


# ─── Funciones de sembrado ───

async def seed_roles(db: AsyncSession) -> dict[str, int]:
    """Crea/actualiza los 5 roles. Retorna {codigo: id}."""
    cache = {}
    for r in ROLES_DATA:
        existing = await db.execute(select(Rol).where(Rol.codigo == r["codigo"]))
        rol = existing.scalar_one_or_none()
        if rol is None:
            rol = Rol(**r)
            db.add(rol)
            print(f"  [+] Rol creado: {r['codigo']}")
        else:
            for k, v in r.items():
                setattr(rol, k, v)
            print(f"  [~] Rol actualizado: {r['codigo']}")
        await db.flush()
        cache[r["codigo"]] = rol.id
    return cache


async def seed_modulos(db: AsyncSession) -> dict[str, int]:
    """Crea/actualiza los 10+1 módulos."""
    cache = {}
    for m in MODULOS_DATA:
        existing = await db.execute(select(Modulo).where(Modulo.codigo == m["codigo"]))
        modulo = existing.scalar_one_or_none()
        if modulo is None:
            modulo = Modulo(**m)
            db.add(modulo)
            print(f"  [+] Modulo creado: {m['codigo']}")
        else:
            for k, v in m.items():
                setattr(modulo, k, v)
            print(f"  [~] Modulo actualizado: {m['codigo']}")
        await db.flush()
        cache[m["codigo"]] = modulo.id
    return cache


async def seed_gerencias(db: AsyncSession) -> dict[str, int]:
    """Crea/actualiza las 10 gerencias."""
    cache = {}
    for sigla, nombre, orden in GERENCIAS_DATA:
        existing = await db.execute(select(Gerencia).where(Gerencia.sigla == sigla))
        gerencia = existing.scalar_one_or_none()
        if gerencia is None:
            gerencia = Gerencia(sigla=sigla, nombre=nombre, orden=orden, activo=True)
            db.add(gerencia)
            print(f"  [+] Gerencia creada: {sigla} - {nombre}")
        else:
            gerencia.nombre = nombre
            gerencia.orden = orden
            print(f"  [~] Gerencia actualizada: {sigla}")
        await db.flush()
        cache[sigla] = gerencia.id
    return cache


async def seed_areas(db: AsyncSession, gerencias_cache: dict[str, int]) -> dict[str, int]:
    """Crea/actualiza las áreas. Retorna {sigla_area: id}."""
    cache = {}
    for gerencia_sigla, sigla, nombre, orden in AREAS_DATA:
        existing = await db.execute(select(Area).where(Area.sigla == sigla))
        area = existing.scalar_one_or_none()
        if area is None:
            area = Area(
                gerencia_id=gerencias_cache[gerencia_sigla],
                sigla=sigla, nombre=nombre, orden=orden, activo=True,
            )
            db.add(area)
            print(f"  [+] Area creada: {sigla} ({gerencia_sigla}) - {nombre}")
        else:
            area.gerencia_id = gerencias_cache[gerencia_sigla]
            area.nombre = nombre
            area.orden = orden
            print(f"  [~] Area actualizada: {sigla}")
        await db.flush()
        cache[sigla] = area.id
    return cache


async def seed_usuarios_stub(
    db: AsyncSession,
    roles_cache: dict[str, int],
    areas_cache: dict[str, int],
) -> None:
    """Crea los 4 usuarios de desarrollo."""
    from app.models.usuario import usuario_roles

    for u in USUARIOS_STUB_DATA:
        existing = await db.execute(
            select(Usuario).where(Usuario.username == u["username"])
        )
        usuario = existing.scalar_one_or_none()

        # Resolver area
        area_id = None
        if u["area_sigla"]:
            area_id = areas_cache.get(u["area_sigla"])

        if usuario is None:
            usuario = Usuario(
                username=u["username"],
                email=u["email"],
                nombre_completo=u["nombre_completo"],
                iniciales=u["iniciales"],
                cargo=u["cargo"],
                area_id=area_id,
                estado=EstadoUsuario.ACTIVO,
                ausente=False,
                estado_delegacion=u["estado_delegacion"],
                visualiza_reportes=False,
                requiere_delegado=False,
            )
            db.add(usuario)
            print(f"  [+] Usuario creado: {u['username']}")
        else:
            usuario.email = u["email"]
            usuario.nombre_completo = u["nombre_completo"]
            usuario.iniciales = u["iniciales"]
            usuario.cargo = u["cargo"]
            usuario.area_id = area_id
            usuario.estado_delegacion = u["estado_delegacion"]
            print(f"  [~] Usuario actualizado: {u['username']}")
        await db.flush()

        # Asignar rol
        rol_id = roles_cache[u["rol"]]
        await db.execute(
            usuario_roles.delete().where(usuario_roles.c.usuario_id == usuario.id)
        )
        await db.execute(
            usuario_roles.insert().values(usuario_id=usuario.id, rol_id=rol_id)
        )

        # Sesion 26: modulo por usuario eliminado (era codigo muerto).
        # El control de acceso es por ROL via ACL hardcodeado en el frontend
        # (auth.js:canAccess). El campo u["modulos"] se conserva en el dict
        # como metadata/documentacion pero no se persiste.
        print(f"    - Rol: {u['rol']}")
        print(f"    - Módulos (metadata, no se persisten): {len(u['modulos'])}")


async def main() -> None:
    print("=" * 60)
    print("COFAR SGD - Seed Data")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        try:
            print("\n[1/5] Sembrando roles...")
            roles_cache = await seed_roles(db)

            print("\n[2/5] Sembrando módulos...")
            modulos_cache = await seed_modulos(db)

            print("\n[3/5] Sembrando gerencias...")
            gerencias_cache = await seed_gerencias(db)

            print("\n[4/5] Sembrando áreas...")
            areas_cache = await seed_areas(db, gerencias_cache)

            print("\n[5/5] Sembrando usuarios stub...")
            await seed_usuarios_stub(db, roles_cache, areas_cache)

            await db.commit()
            print("\n" + "=" * 60)
            print("Seed completado con éxito.")
            print("=" * 60)
        except Exception as e:
            await db.rollback()
            print(f"\nError durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
