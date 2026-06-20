"""add semaforizacion_tarea table

Sesion 13 (2026-06-16): nueva tabla para reglas de semaforo por tipo de tarea.
Reemplaza las 2 claves globales en `configuracion_global` (semaforo_verde_dias,
semaforo_amarillo_dias) que aplicaban a TODAS las tareas por una fila por
tipo de tarea con sus propios umbrales.

Revision ID: f04b96c6dff2
Revises: 6b244889632f
Create Date: 2026-06-16 23:57:23.715900
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f04b96c6dff2'
down_revision: Union[str, None] = '6b244889632f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'semaforizacion_tarea',
        sa.Column('tipo_tarea', sa.Enum('REVISION', 'APROBACION', 'CONTROL_LECTURA', 'EVALUACION', name='tipo_tarea_semaforo'), nullable=False),
        sa.Column('dias_verde', sa.Integer(), nullable=False),
        sa.Column('dias_amarillo', sa.Integer(), nullable=False),
        sa.Column('dias_rojo', sa.Integer(), nullable=False),
        sa.Column('plazo_maximo_dias', sa.Integer(), nullable=False),
        sa.Column('descripcion', sa.String(length=500), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('tipo_tarea'),
    )
    # Sembrar las 4 reglas (idempotente, OK si ya hay datos via seed)
    op.execute("""
        INSERT INTO semaforizacion_tarea
            (tipo_tarea, dias_verde, dias_amarillo, dias_rojo, plazo_maximo_dias, descripcion, activo, created_at, updated_at)
        VALUES
            ('REVISION', 7, 12, 15, 15, 'Verde 0-7, Amarillo 8-12, Rojo 13-15 (faltan 3 dias para cumplir plazo)', true, now(), now()),
            ('APROBACION', 7, 12, 15, 15, 'Verde 0-7, Amarillo 8-12, Rojo 13-15 (faltan 3 dias para cumplir plazo)', true, now(), now()),
            ('CONTROL_LECTURA', 7, 12, 15, 15, 'Verde 0-7, Amarillo 8-12, Rojo 13-15 (faltan 3 dias para cumplir plazo)', true, now(), now()),
            ('EVALUACION', 5, 11, 15, 15, 'Verde 0-5, Amarillo 6-11, Rojo 12-15 (faltan 3 dias para cumplir plazo)', true, now(), now())
        ON CONFLICT (tipo_tarea) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table('semaforizacion_tarea')
