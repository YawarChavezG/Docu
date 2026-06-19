"""R3 item 0.2: agregar documento_actualizado_id a documento_flujo

Sesion 36 (R3 Fase 0 - 0.2 Actualizacion documental).
Cuando tipo_solicitud='ACTUALIZACION', el wizard selecciona un documento
existente a actualizar. Este campo guarda el ID del documento original
para trazabilidad y para calcular la version nueva (version_anterior + 1).

Cambios:
1. ALTER TABLE documento_flujo ADD COLUMN documento_actualizado_id INT
   REFERENCES documentos(id) ON DELETE SET NULL.
2. CREATE INDEX ix_flujo_documento_actualizado para queries
   rapidas de "flujos que actualizaron este documento".

Revision ID: r3_doc_actualizado_s36
Revises: r3_liberacion_eto_s36
Create Date: 2026-06-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "r3_doc_actualizado_s36"
down_revision: Union[str, None] = "r3_liberacion_eto_s36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documento_flujo",
        sa.Column("documento_actualizado_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_flujo_documento_actualizado",
        "documento_flujo",
        "documentos",
        ["documento_actualizado_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_flujo_documento_actualizado",
        "documento_flujo",
        ["documento_actualizado_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_flujo_documento_actualizado", table_name="documento_flujo")
    op.drop_constraint("fk_flujo_documento_actualizado", "documento_flujo", type_="foreignkey")
    op.drop_column("documento_flujo", "documento_actualizado_id")
