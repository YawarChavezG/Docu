"""
seed_configuracion_global.py - COFAR SGD (Sesion 12, cierre R1)

Sembra los parametros globales del sistema (US-9.01 + US-9.02):
  - VIGENCIA: tiempo_vigencia_anios, espera_auto_delegacion_dias
  - ARCHIVOS: max_archivos_por_solicitud, max_tamano_archivo_mb
  - DESCARGAS: max_descargas_editables_dia, paginacion_mi_bandeja,
               tipos_excluidos_limite_descarga

NOTA (Sesion 23 / Bloque A5): Las claves plazo_revision_aprobacion_dias,
plazo_control_lectura_dias, semaforo_verde_dias y semaforo_amarillo_dias
fueron removidas del seed porque son REDUNDANTES con la tabla
semaforizacion_tarea (que tiene dias_verde, dias_amarillo, dias_rojo,
plazo_maximo_dias por tipo de tarea). Las 4 claves existentes se
mantienen en BD como activo=false (borrado logico) para preservar
audit_log y referencias historicas.

Idempotente: si la clave ya existe con los valores esperados, no hace nada.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.configuracion_global import (
    ConfiguracionGlobal,
    TipoConfiguracion,
    CategoriaConfiguracion,
)


# (clave, valor, tipo, categoria, descripcion)
PARAMETROS = [
    # VIGENCIA
    ("tiempo_vigencia_anios",          "3",  TipoConfiguracion.INT, CategoriaConfiguracion.VIGENCIA, "Anios de vigencia por defecto de un documento"),
    ("espera_auto_delegacion_dias",    "3",  TipoConfiguracion.INT, CategoriaConfiguracion.VIGENCIA, "Dias de espera antes de auto-delegar (US-9.05)"),
    # ARCHIVOS
    ("max_archivos_por_solicitud",     "20", TipoConfiguracion.INT, CategoriaConfiguracion.ARCHIVOS, "Cantidad maxima de archivos adjuntos por solicitud"),
    ("max_tamano_archivo_mb",          "20", TipoConfiguracion.INT, CategoriaConfiguracion.ARCHIVOS, "Tamano maximo por archivo individual en MB"),
    # DESCARGAS
    ("max_descargas_editables_dia",    "10", TipoConfiguracion.INT, CategoriaConfiguracion.DESCARGAS, "Maximo de descargas de editable por dia por usuario"),
    ("paginacion_mi_bandeja",          "10", TipoConfiguracion.INT, CategoriaConfiguracion.DESCARGAS, "Registros por pagina en Mi Bandeja"),
    ("tipos_excluidos_limite_descarga","[]", TipoConfiguracion.JSON, CategoriaConfiguracion.DESCARGAS, "Array JSON de codigos de tipo_documento excluidos del limite de descarga"),
]


async def seed_parametros(db) -> tuple[int, int]:
    creados = 0
    actualizados = 0
    for clave, valor, tipo, categoria, descripcion in PARAMETROS:
        existing = (await db.execute(
            select(ConfiguracionGlobal).where(ConfiguracionGlobal.clave == clave)
        )).scalar_one_or_none()

        if existing is None:
            c = ConfiguracionGlobal(
                clave=clave, valor=valor, tipo=tipo,
                categoria=categoria, descripcion=descripcion, activo=True,
            )
            db.add(c)
            print(f"  [+] {clave:35} {valor:>6}  ({categoria.value})")
            creados += 1
        else:
            changed = False
            if existing.valor != valor: existing.valor = valor; changed = True
            if existing.tipo != tipo: existing.tipo = tipo; changed = True
            if existing.categoria != categoria: existing.categoria = categoria; changed = True
            if existing.descripcion != descripcion: existing.descripcion = descripcion; changed = True
            # Solo re-activar si esta inactivo por error. NO reactivar las 4
            # claves redundantes (Sesion 23 Bloque A5) aunque esten en BD.
            claves_redundantes_inactivas = {
                "plazo_revision_aprobacion_dias",
                "plazo_control_lectura_dias",
                "semaforo_verde_dias",
                "semaforo_amarillo_dias",
            }
            if not existing.activo and clave not in claves_redundantes_inactivas:
                existing.activo = True
                changed = True
            if changed:
                print(f"  [~] {clave:35} actualizado")
                actualizados += 1
            else:
                print(f"  [=] {clave:35} sin cambios")
        await db.flush()
    return creados, actualizados


async def main() -> None:
    print("=" * 70)
    print("COFAR SGD - Seed Configuracion Global (US-9.01 + US-9.02)")
    print("=" * 70)
    print(f"Total: {len(PARAMETROS)} parametros")

    async with AsyncSessionLocal() as db:
        try:
            creados, actualizados = await seed_parametros(db)
            await db.commit()
            print("\n" + "=" * 70)
            print(f"Resultado: {creados} creados, {actualizados} actualizados")
            print("=" * 70)
        except Exception as e:
            await db.rollback()
            print(f"\nError durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
