"""R3 item 0.6: agregar LIBERACION_ETO al enum estatus_documento

Sesion 36 (R3 Fase 0 - 0.6 Flujo post-wizard: va a ETO primero).
Cambio el flujo del documento: despues de firmar el wizard (paso 3),
el documento pasa a LIBERACION_ETO (a la bandeja de ETO) en vez de ir
directo a EN_REVISION (revisores). Solo cuando ETO libera (futuro
endpoint POST /documentos/{id}/liberar, R3 Fase 1) el documento pasa
a EN_REVISION y se crean las tareas para los revisores.

Cambios:
1. ALTER TYPE estatus_documento ADD VALUE 'LIBERACION_ETO'
2. Ningun cambio de tabla (es solo un valor nuevo del enum PostgreSQL).

Revision ID: r3_liberacion_eto_s36
Revises: drop_modulos_s26
Create Date: 2026-06-19
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "r3_liberacion_eto_s36"
down_revision: Union[str, None] = "drop_modulos_s26"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # AGREGAR valor al enum PostgreSQL estatus_documento.
    # PG requiere autocommit=True para ALTER TYPE ... ADD VALUE fuera de una tx
    # (un valor nuevo no se puede usar en la misma tx donde se agrega).
    # IF NOT EXISTS para que sea idempotente (seguro re-correr).
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE estatus_documento ADD VALUE IF NOT EXISTS 'LIBERACION_ETO'")


def downgrade() -> None:
    # PostgreSQL < 12 NO soporta DROP VALUE. En PG 16 tampoco es trivial
    # porque el valor podria estar en uso en filas existentes.
    # Para esta sesion no necesitamos un downgrade real — si se hace rollback,
    # el valor 'LIBERACION_ETO' queda en el enum sin uso (no rompe nada).
    # Documentado en DECISIONES.md (ADR-069 candidato).
    pass
