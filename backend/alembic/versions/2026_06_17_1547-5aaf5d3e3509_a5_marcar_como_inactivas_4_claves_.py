"""A5: marcar como inactivas 4 claves redundantes de semaforizacion

Las claves plazo_revision_aprobacion_dias, plazo_control_lectura_dias,
semaforo_verde_dias y semaforo_amarillo_dias en configuracion_global son
redundantes con la tabla semaforizacion_tarea (que ahora tiene dias_verde,
dias_amarillo, dias_rojo, plazo_maximo_dias por tipo de tarea).

Se hace borrado LOGICO (activo=false) para preservar audit_log y posibles
referencias en documentacion historica. No se borran fisicamente.

Revision ID: 5aaf5d3e3509
Revises: b88801d59687
Create Date: 2026-06-17 15:47:38.118502
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5aaf5d3e3509"
down_revision: Union[str, None] = "b88801d59687"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CLAVES_A_DESACTIVAR = [
    "plazo_revision_aprobacion_dias",
    "plazo_control_lectura_dias",
    "semaforo_verde_dias",
    "semaforo_amarillo_dias",
]


def upgrade() -> None:
    # Borrado logico: marcar activo=false (no se borra fisicamente)
    op.execute(
        "UPDATE configuracion_global SET activo = false "
        "WHERE clave IN ('plazo_revision_aprobacion_dias', "
        "'plazo_control_lectura_dias', 'semaforo_verde_dias', "
        "'semaforo_amarillo_dias')"
    )


def downgrade() -> None:
    # Reactivar las claves por si se hace rollback
    op.execute(
        "UPDATE configuracion_global SET activo = true "
        "WHERE clave IN ('plazo_revision_aprobacion_dias', "
        "'plazo_control_lectura_dias', 'semaforo_verde_dias', "
        "'semaforo_amarillo_dias')"
    )
