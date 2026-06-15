"""
Seed de 5 usuarios locales para DES.

Estos usuarios NO son del AD — viven solo en la BD local y se loguean
con la password dummy `cofar.2026` (modo DES del auth).

¿Para qué sirven?
- Probar el frontend sin depender de la VPN / AD.
- Tener 1 usuario de cada rol (ADMIN, ETO, ELABORADOR-REVISOR,
  ELABORADOR-REVISOR-APROBADOR, VISUALIZADOR-CL-EVAL) para validar
  que el RBAC funciona.
- Tener `admin_local` con pass `admin.2026` (placeholder) para uso
  explícito del dev. Por ahora ambos (admin_local y los 4 con
  cofar.2026) usan la misma pass `cofar.2026` en modo DES hasta
  que implementemos pass locales reales.

Idempotente: corre múltiples veces sin duplicar.

Uso:
    docker exec sgd-backend python scripts/seed_local_test_users.py
  o con el backend nativo:
    cd backend && python scripts/seed_local_test_users.py
"""
import asyncio
import sys
from pathlib import Path

# Make 'app' importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.rol import CodigoRol
from app.models.modulo import CodigoModulo
from app.models.usuario import Usuario, EstadoUsuario, EstadoDelegacion
from app.models.gerencia import Gerencia
from app.models.area import Area

# ─── Usuarios a sembrar ───
# Todos usan pass `cofar.2026` en modo DES (hardcoded en auth.py).
# El password_hash queda como placeholder para futuro.

USUARIOS_LOCALES = [
    {
        "username": "admin_local",
        "email": "admin_local@cofar.local",
        "nombre_completo": "Carlos Mendoza",
        "iniciales": "CM",
        "cargo": "Administrador del Sistema (local)",
        "gerencia_sigla": "GAD",
        "area_sigla": "ADM",
        "rol": CodigoRol.ADMIN,
        "modulos": [CodigoModulo.TODOS],
        "estado_delegacion": EstadoDelegacion.NA,
        "password_hash_placeholder": "admin.2026",
    },
    {
        "username": "eto_test",
        "email": "eto_test@cofar.local",
        "nombre_completo": "Patricia Vargas",
        "iniciales": "PV",
        "cargo": "Gestor Documental ETO (test)",
        "gerencia_sigla": "GTE",
        "area_sigla": "ETO",
        "rol": CodigoRol.ETO,
        "modulos": [CodigoModulo.TODOS],
        "estado_delegacion": EstadoDelegacion.NA,
        "password_hash_placeholder": "cofar.2026",
    },
    {
        "username": "elaborador_revisor",
        "email": "elaborador_revisor@cofar.local",
        "nombre_completo": "Roberto Silva",
        "iniciales": "RS",
        "cargo": "Analista de Control de Calidad",
        "gerencia_sigla": "GTE",
        "area_sigla": "CC",
        "rol": CodigoRol.ELABORADOR_REVISOR,
        "modulos": [
            CodigoModulo.MI_BANDEJA, CodigoModulo.LISTA_MAESTRA,
            CodigoModulo.CONSULTAR_DOCUMENTOS, CodigoModulo.MIS_EVALUACIONES,
            CodigoModulo.NUEVA_SOLICITUD, CodigoModulo.PLANTILLAS_DOCUMENTALES,
            CodigoModulo.ASISTENTE_IA,
        ],
        "estado_delegacion": EstadoDelegacion.PENDIENTE,
        "password_hash_placeholder": "cofar.2026",
    },
    {
        "username": "elaborador_revisor_aprobador",
        "email": "elaborador_revisor_aprobador@cofar.local",
        "nombre_completo": "Mónica Fernández",
        "iniciales": "MF",
        "cargo": "Jefe de Validaciones Farmacéuticas",
        "gerencia_sigla": "GTE",
        "area_sigla": "VAL",
        "rol": CodigoRol.ELABORADOR_REVISOR_APROBADOR,
        "modulos": [
            CodigoModulo.MI_BANDEJA, CodigoModulo.LISTA_MAESTRA,
            CodigoModulo.CONSULTAR_DOCUMENTOS, CodigoModulo.MIS_EVALUACIONES,
            CodigoModulo.NUEVA_SOLICITUD, CodigoModulo.PLANTILLAS_DOCUMENTALES,
            CodigoModulo.ASISTENTE_IA,
        ],
        "estado_delegacion": EstadoDelegacion.PENDIENTE,
        "password_hash_placeholder": "cofar.2026",
    },
    {
        "username": "visualizador_cl",
        "email": "visualizador_cl@cofar.local",
        "nombre_completo": "Diego Quispe",
        "iniciales": "DQ",
        "cargo": "Operario Planta Sólidos",
        "gerencia_sigla": "GCO",
        "area_sigla": "PLA",
        "rol": CodigoRol.VISUALIZADOR_CL_EVAL,
        "modulos": [
            CodigoModulo.BANDEJA_TAREAS, CodigoModulo.LISTA_MAESTRA,
            CodigoModulo.MIS_EVALUACIONES, CodigoModulo.ASISTENTE_IA,
        ],
        "estado_delegacion": EstadoDelegacion.NA,
        "password_hash_placeholder": "cofar.2026",
    },
]


async def get_or_create_usuario(
    db: AsyncSession, u: dict, areas_cache: dict[str, int]
) -> Usuario:
    """Crea o actualiza un usuario local de test."""
    from app.models.usuario import usuario_roles, usuario_modulos

    result = await db.execute(select(Usuario).where(Usuario.username == u["username"]))
    usuario = result.scalar_one_or_none()

    area_id = areas_cache.get(u["area_sigla"]) if u.get("area_sigla") else None

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
            password_hash=f"DES_PLACEHOLDER:{u['password_hash_placeholder']}",  # Marcador, no usado en modo DES
        )
        db.add(usuario)
        print(f"  [+] Usuario creado: {u['username']} ({u['nombre_completo']})")
    else:
        usuario.email = u["email"]
        usuario.nombre_completo = u["nombre_completo"]
        usuario.iniciales = u["iniciales"]
        usuario.cargo = u["cargo"]
        usuario.area_id = area_id
        usuario.estado_delegacion = u["estado_delegacion"]
        print(f"  [~] Usuario actualizado: {u['username']}")
    await db.flush()

    # ─── Asignar rol ───
    from app.models.rol import Rol
    rol_result = await db.execute(select(Rol).where(Rol.codigo == u["rol"]))
    rol = rol_result.scalar_one()
    await db.execute(
        usuario_roles.delete().where(usuario_roles.c.usuario_id == usuario.id)
    )
    await db.execute(
        usuario_roles.insert().values(usuario_id=usuario.id, rol_id=rol.id)
    )

    # ─── Asignar módulos ───
    from app.models.modulo import Modulo
    await db.execute(
        usuario_modulos.delete().where(usuario_modulos.c.usuario_id == usuario.id)
    )
    for modulo_codigo in u["modulos"]:
        mod_result = await db.execute(select(Modulo).where(Modulo.codigo == modulo_codigo))
        mod = mod_result.scalar_one()
        await db.execute(
            usuario_modulos.insert().values(usuario_id=usuario.id, modulo_id=mod.id)
        )

    print(f"    - Rol: {u['rol']}")
    print(f"    - Módulos: {len(u['modulos'])}")
    print(f"    - Área: {u.get('area_sigla', '-')} (gerencia {u.get('gerencia_sigla', '-')})")
    return usuario


async def main() -> None:
    print("=" * 60)
    print("COFAR SGD - Seed de 5 usuarios locales de test")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        try:
            # ─── Resolver áreas por sigla ───
            print("\n[1/2] Resolviendo áreas...")
            areas_cache: dict[str, int] = {}
            for u in USUARIOS_LOCALES:
                if u.get("area_sigla") and u["area_sigla"] not in areas_cache:
                    result = await db.execute(
                        select(Area).where(Area.sigla == u["area_sigla"])
                    )
                    area = result.scalar_one_or_none()
                    if area:
                        areas_cache[u["area_sigla"]] = area.id
                        print(f"  [OK] Área {u['area_sigla']} -> id {area.id}")
                    else:
                        print(f"  [WARN] Área {u['area_sigla']} no existe. Se creará sin área.")

            # ─── Sembrar usuarios ───
            print("\n[2/2] Sembrando usuarios locales...")
            for u in USUARIOS_LOCALES:
                await get_or_create_usuario(db, u, areas_cache)

            await db.commit()
            print("\n" + "=" * 60)
            print("Seed completado. 5 usuarios locales listos.")
            print("=" * 60)
            print("\nLogin con cualquiera de estos usuarios + pass 'cofar.2026':")
            for u in USUARIOS_LOCALES:
                print(f"  - {u['username']:<35} ({u['rol']})")
            print("\nNOTA: Todos usan pass 'cofar.2026' en modo DES.")
            print("El 'admin_local' tiene un placeholder 'admin.2026' documentado,")
            print("pero ambos usan la misma pass hasta que se implemente pass local real.")
            print("=" * 60)
        except Exception as e:
            await db.rollback()
            print(f"\nError durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
