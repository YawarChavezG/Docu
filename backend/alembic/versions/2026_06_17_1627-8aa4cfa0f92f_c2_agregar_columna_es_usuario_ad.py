"""C2: agregar columna es_usuario_ad

Sesion 23 / Bloque C2 (reunion con cliente):
Distingue usuarios importados/creados desde el AD de los sembrados
manualmente (stubs de DES, admin_local, etc).

Reglas:
- True: usuario creado por sync-ad O por login on-the-fly desde LDAP
- False: usuario creado por seed_data.py, admin_local, etc.

Tambien backfill: marcar True a todos los usuarios que tienen ad_postal_code
(ya importados via sync) y False a los que NO (sembrados manualmente).

Revision ID: 8aa4cfa0f92f
Revises: 353aec067661
Create Date: 2026-06-17 16:27:17.219794
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8aa4cfa0f92f"
down_revision: Union[str, None] = "353aec067661"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Agregar la columna con default False
    op.add_column(
        "usuarios",
        sa.Column(
            "es_usuario_ad",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index("ix_usuarios_es_usuario_ad", "usuarios", ["es_usuario_ad"])

    # 2) Backfill: usuarios con ad_postal_code IS NOT NULL son del AD
    op.execute("UPDATE usuarios SET es_usuario_ad = true WHERE ad_postal_code IS NOT NULL")


def downgrade() -> None:
    op.drop_index("ix_usuarios_es_usuario_ad", table_name="usuarios")
    op.drop_column("usuarios", "es_usuario_ad")
