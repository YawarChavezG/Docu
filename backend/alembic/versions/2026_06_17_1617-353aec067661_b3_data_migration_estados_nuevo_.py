"""B3: data-migration estados + nuevo contexto ACCION

Sesion 23 / Bloque B3 (reunion con cliente):
- Eliminar los 9 estados actuales: Correccion, Liberacion ETO, Revision,
  Concluido, Anulado, Aprobacion, y los 3 de prueba (TST1, TE_26664, TEST_NUEVO).
- Crear 12 nuevos estados con sus contextos:
  * PROCESO (3): Concluido, En Ejecucion, Eliminado
  * TAREA (6): Solicitud Creada, Liberacion ETO, Revision, Aprobado, Eliminacion, Correccion
  * ACCION (3): Ejecutado, Pendiente, Eliminado

Se hace borrado LOGICO (activo=false) de los antiguos para preservar audit_log
y referencias historicas. Los 12 nuevos se insertan con orden correlativo.

Revision ID: 353aec067661
Revises: 5aaf5d3e3509
Create Date: 2026-06-17 16:17:11.343120
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "353aec067661"
down_revision: Union[str, None] = "5aaf5d3e3509"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Estados antiguos a desactivar (borrado logico)
ESTADOS_ANTIGUOS_A_DESACTIVAR = [
    "ELABORACION",
    "LIBERACION_ETO",
    "REVISION_PARALELA",
    "FINALIZADO",
    "ANULADO",
    "APROBACION",
    "TST1",
    "TE_26664",
    "TEST_NUEVO",
]

# Estados nuevos: (codigo, nombre, contexto, orden, descripcion)
ESTADOS_NUEVOS = [
    # ─── PROCESO (3) ───
    ("CONCLUIDO",        "Concluido",        "PROCESO", 1, "Proceso completado y cerrado de forma exitosa"),
    ("EN_EJECUCION",     "En Ejecucion",     "PROCESO", 2, "Proceso en ejecucion, aun con tareas pendientes"),
    ("ELIMINADO_PROC",   "Eliminado",        "PROCESO", 3, "Proceso eliminado (borrado logico)"),

    # ─── TAREA (6) ───
    ("SOLICITUD_CREADA", "Solicitud Creada", "TAREA",   10, "Tarea recien creada, pendiente de liberar"),
    ("LIBERACION_ETO",   "Liberacion ETO",   "TAREA",   20, "Tarea en etapa de liberacion por ETO"),
    ("REVISION",         "Revision",         "TAREA",   30, "Tarea en etapa de revision"),
    ("APROBADO",         "Aprobado",         "TAREA",   40, "Tarea aprobada, pendiente de difusion/ejecucion"),
    ("ELIMINACION",      "Eliminacion",      "TAREA",   50, "Tarea eliminada (borrado logico)"),
    ("CORRECCION",       "Correccion",       "TAREA",   60, "Tarea devuelta para correcciones"),

    # ─── ACCION (3) ───
    ("EJECUTADO",        "Ejecutado",        "ACCION",  1, "Accion ejecutada por el usuario asignado"),
    ("PENDIENTE",        "Pendiente",        "ACCION",  2, "Accion pendiente de ejecucion"),
    ("ELIMINADO_ACC",    "Eliminado",        "ACCION",  3, "Accion eliminada (borrado logico)"),
]


def upgrade() -> None:
    # 0) Agregar valor 'ACCION' al enum contexto_estado (Sesion 23 / Bloque B3)
    #    Necesario porque el modelo Python ahora tiene ContextoEstado.ACCION
    #    pero la columna de la BD no lo tiene.
    #    PG requiere autocommit=True para ALTER TYPE ... ADD VALUE fuera de
    #    una transaccion (un valor nuevo no se puede usar en la misma tx).
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE contexto_estado ADD VALUE IF NOT EXISTS 'ACCION'")

    # 1) Borrado logico de los antiguos
    codigos_sql = ", ".join(f"'{c}'" for c in ESTADOS_ANTIGUOS_A_DESACTIVAR)
    op.execute(f"UPDATE estados SET activo = false WHERE codigo IN ({codigos_sql})")

    # 2) Insertar los 12 nuevos (idempotente via ON CONFLICT)
    for codigo, nombre, contexto, orden, descripcion in ESTADOS_NUEVOS:
        op.execute(
            sa.text(
                """
                INSERT INTO estados (codigo, nombre, contexto, orden, descripcion, activo)
                VALUES (:codigo, :nombre, CAST(:contexto AS contexto_estado), :orden, :descripcion, true)
                ON CONFLICT (codigo) DO UPDATE
                  SET nombre = EXCLUDED.nombre,
                      contexto = EXCLUDED.contexto,
                      orden = EXCLUDED.orden,
                      descripcion = EXCLUDED.descripcion,
                      activo = true
                """
            ).bindparams(
                codigo=codigo,
                nombre=nombre,
                contexto=contexto,
                orden=orden,
                descripcion=descripcion,
            )
        )


def downgrade() -> None:
    # 1) Borrar los nuevos insertados en esta migracion
    codigos_nuevos_sql = ", ".join(f"'{e[0]}'" for e in ESTADOS_NUEVOS)
    op.execute(f"DELETE FROM estados WHERE codigo IN ({codigos_nuevos_sql})")
    # 2) Reactivar los antiguos
    codigos_sql = ", ".join(f"'{c}'" for c in ESTADOS_ANTIGUOS_A_DESACTIVAR)
    op.execute(f"UPDATE estados SET activo = true WHERE codigo IN ({codigos_sql})")
    # NOTA: no se puede quitar 'ACCION' del enum en PostgreSQL con un ALTER
    # TYPE DROP VALUE (no soportado en versiones < 12 ni en PG 16 con CASCADE).
    # Si se hace rollback completo, queda el valor 'ACCION' en el enum sin usar.
