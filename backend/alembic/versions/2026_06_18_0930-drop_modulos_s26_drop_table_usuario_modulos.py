"""S26: drop table usuario_modulos

Sesion 26 / Cleanup BD: el cliente decidio eliminar la tabla
usuario_modulos porque era codigo muerto. El control de acceso en el
frontend se hace por ROL via ACL hardcodeado (auth.js:canAccess), no
por los modulos del usuario. El campo user.modulos del backend nunca
se leia en el frontend (solo se recibia y se ignoraba).

Ademas:
- Los 3 modulos "antiguos" (ASISTENTE_IA, LISTA_MAESTRA, MIS_EVALUACIONES)
  estaban asignados a 724 usuarios (probablemente del import de la
  matriz abril - sesion 8), lo cual inflaba la BD innecesariamente.
- El script de import (matriz_import_service.py) ya no asigna modulos.

Revision ID: drop_modulos_s26
Revises: 8aa4cfa0f92f
Create Date: 2026-06-18 09:30:00.000000
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "drop_modulos_s26"
down_revision: Union[str, None] = "8aa4cfa0f92f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # DROP TABLE con CASCADE para no romper si hay dependencias en otros schemas
    op.execute("DROP TABLE IF EXISTS usuario_modulos CASCADE")


def downgrade() -> None:
    # Re-crear la tabla con la estructura original (para rollback)
    op.execute("""
        CREATE TABLE usuario_modulos (
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            modulo_id INTEGER NOT NULL REFERENCES modulos(id) ON DELETE CASCADE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            PRIMARY KEY (usuario_id, modulo_id)
        )
    """)
