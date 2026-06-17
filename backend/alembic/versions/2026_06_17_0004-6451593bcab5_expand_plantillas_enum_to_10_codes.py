"""expand plantillas enum to 10 codes (sesion 13)

Antes: 6 plantillas (NUEVA_TAREA, ALERTA_VENCIMIENTO, DOCUMENTO_APROBADO,
DOCUMENTO_OBSERVADO, EVALUACION_PENDIENTE, AUTO_DELEGACION_ACTIVADA).

Ahora: 10 plantillas del documento `docs/PR/PLANTILLAS DE NOTIFICACION.md`
+ AUTO_DELEGACION_ACTIVADA (mantenido del PDF original).

Revision ID: 6451593bcab5
Revises: f04b96c6dff2
Create Date: 2026-06-17 00:04:51.250910

Estrategia:
  1. Borrar TODAS las filas de email_templates (los 6 codigos viejos
     no estan en el nuevo enum; no se pueden migrar automaticamente
     porque los codigos son diferentes).
  2. DROP TYPE codigo_plantilla.
  3. CREATE TYPE codigo_plantilla AS ENUM con los 11 valores nuevos.
  4. ALTER COLUMN para que use el nuevo tipo.
  5. (El seed externo seed_email_templates.py re-puebla con el contenido
     del documento oficial.)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6451593bcab5'
down_revision: Union[str, None] = 'f04b96c6dff2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_VALUES = [
    'ASIG_REVISION',
    'ASIG_APROBACION',
    'SOLICITUD_CORRECCION',
    'CONTROL_LECTURA',
    'EVALUACION_ASIGNADA',
    'LIBERACION_DOCUMENTO',
    'DOCUMENTO_APROBADO',
    'REASIG_INCUMPLIMIENTO',
    'REASIG_MANUAL',
    'TAREA_PROXIMA_VENCER',
    'AUTO_DELEGACION_ACTIVADA',
]

OLD_VALUES = [
    'NUEVA_TAREA',
    'ALERTA_VENCIMIENTO',
    'DOCUMENTO_APROBADO',
    'DOCUMENTO_OBSERVADO',
    'EVALUACION_PENDIENTE',
    'AUTO_DELEGACION_ACTIVADA',
]


def upgrade() -> None:
    # 1. Borrar todas las filas de email_templates (los codigos viejos ya
    #    no existen en el nuevo enum; el seed los re-puebla).
    op.execute("DELETE FROM email_templates")

    # 2. ALTER COLUMN a text temporalmente
    op.execute("ALTER TABLE email_templates ALTER COLUMN codigo TYPE VARCHAR(40)")

    # 3. DROP TYPE viejo y crear nuevo
    op.execute("DROP TYPE IF EXISTS codigo_plantilla")
    enum_values = ", ".join(f"'{v}'" for v in NEW_VALUES)
    op.execute(f"CREATE TYPE codigo_plantilla AS ENUM ({enum_values})")

    # 4. ALTER COLUMN al nuevo enum
    op.execute("ALTER TABLE email_templates ALTER COLUMN codigo TYPE codigo_plantilla USING codigo::codigo_plantilla")


def downgrade() -> None:
    # 1. ALTER a text
    op.execute("ALTER TABLE email_templates ALTER COLUMN codigo TYPE VARCHAR(40)")

    # 2. DROP y recreate viejo
    op.execute("DROP TYPE IF EXISTS codigo_plantilla")
    enum_values = ", ".join(f"'{v}'" for v in OLD_VALUES)
    op.execute(f"CREATE TYPE codigo_plantilla AS ENUM ({enum_values})")

    # 3. ALTER al viejo enum
    op.execute("ALTER TABLE email_templates ALTER COLUMN codigo TYPE codigo_plantilla USING codigo::codigo_plantilla")
