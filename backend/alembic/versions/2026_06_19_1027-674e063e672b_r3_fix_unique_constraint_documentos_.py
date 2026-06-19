"""r3_fix_unique_constraint_documentos_include_version

Permite que en ACTUALIZACION documental existan 2 filas con el mismo
(area_id, tipo_documento_id, correlativo) pero distinta version.

Revision ID: 674e063e672b
Revises: r3_doc_actualizado_s36
Create Date: 2026-06-19 10:27:27.955198
"""
from typing import Sequence, Union
from alembic import op

revision: str = '674e063e672b'
down_revision: Union[str, None] = 'r3_doc_actualizado_s36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old constraint (area, tipo, correlativo) sin version
    op.drop_constraint(
        "uq_documento_area_tipo_correlativo",
        "documentos",
        type_="unique",
    )
    # Add new constraint incluyendo version
    op.create_unique_constraint(
        "uq_documento_area_tipo_correlativo_version",
        "documentos",
        ["area_id", "tipo_documento_id", "correlativo", "version"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_documento_area_tipo_correlativo_version",
        "documentos",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_documento_area_tipo_correlativo",
        "documentos",
        ["area_id", "tipo_documento_id", "correlativo"],
    )
