"""R3 sesion 37: crear tabla plantillas + seed desde disco

Revision ID: r3_plantillas_table_s37
Revises: r3_fase1_fix_semaforo_s37
Create Date: 2026-06-19 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "r3_plantillas_table_s37"
down_revision: Union[str, None] = "r3_fase1_fix_semaforo_s37"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "plantillas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre_archivo", sa.String(length=255), nullable=False),
        sa.Column("nombre_display", sa.String(length=200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("tamano_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mime_type", sa.String(length=100), nullable=False, server_default="application/octet-stream"),
        sa.Column("storage_path", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre_archivo", name="uq_plantilla_nombre_archivo"),
    )
    op.create_index("ix_plantilla_activo", "plantillas", ["activo"])
    op.create_index("ix_plantilla_nombre_archivo", "plantillas", ["nombre_archivo"])


def downgrade() -> None:
    op.drop_index("ix_plantilla_nombre_archivo", table_name="plantillas")
    op.drop_index("ix_plantilla_activo", table_name="plantillas")
    op.drop_table("plantillas")
