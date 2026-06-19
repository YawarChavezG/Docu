"""R3 Fase 1 fix (sesion 37): corregir valores semaforizacion a dias naturales

Corrige la data migration de la migracion r3_fase1_s37 que cambio los
valores de semaforizacion_tarea de dias NATURALES (7/12/15) a dias
HABILES (4/7/10).

La decision del cliente (confirmada en sesion 37):
- Los valores 7/12/15 son dias NATURALES/calendario ≈ 10 habiles.
- El flag usa_dias_habiles debe ser FALSE porque son calendario.
- LIBERACION: ETO no tiene plazo → 999/999/999 (US-1.05).
- CORRECCION: mismo SLA que REVISION → 7/12/15 (US-3.04).

Ademas:
- ALTER COLUMN usa_dias_habiles server_default de true a false.

Revision ID: r3_fase1_fix_semaforo_s37
Revises: r3_fase1_s37
Create Date: 2026-06-19 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "r3_fase1_fix_semaforo_s37"
down_revision: Union[str, None] = "r3_fase1_s37"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── 1. REVISION: restaurar 7/12/15, usa_dias_habiles = FALSE ───
    op.execute(
        "UPDATE semaforizacion_tarea "
        "SET dias_verde = 7, dias_amarillo = 12, dias_rojo = 15, "
        "    plazo_maximo_dias = 15, usa_dias_habiles = FALSE, "
        "    descripcion = 'Legacy: 7/12/15 dias naturales ≈ 10 habiles' "
        "WHERE tipo_tarea = 'REVISION'"
    )

    # ─── 2. APROBACION: restaurar 7/12/15, usa_dias_habiles = FALSE ───
    op.execute(
        "UPDATE semaforizacion_tarea "
        "SET dias_verde = 7, dias_amarillo = 12, dias_rojo = 15, "
        "    plazo_maximo_dias = 15, usa_dias_habiles = FALSE, "
        "    descripcion = 'Legacy: 7/12/15 dias naturales ≈ 10 habiles' "
        "WHERE tipo_tarea = 'APROBACION'"
    )

    # ─── 3. CONTROL_LECTURA: mantener 14/24/30, usa_dias_habiles = FALSE ───
    op.execute(
        "UPDATE semaforizacion_tarea "
        "SET usa_dias_habiles = FALSE, "
        "    descripcion = 'Legacy: 14/24/30 dias naturales (US-6.03)' "
        "WHERE tipo_tarea = 'CONTROL_LECTURA'"
    )

    # ─── 4. EVALUACION: mantener 5/11/15, usa_dias_habiles = FALSE ───
    op.execute(
        "UPDATE semaforizacion_tarea "
        "SET usa_dias_habiles = FALSE, "
        "    descripcion = 'Legacy: 5/11/15 dias naturales' "
        "WHERE tipo_tarea = 'EVALUACION'"
    )

    # ─── 5. LIBERACION: ETO no tiene plazo (US-1.05) ───
    op.execute(
        "UPDATE semaforizacion_tarea "
        "SET dias_verde = 999, dias_amarillo = 999, dias_rojo = 999, "
        "    plazo_maximo_dias = 999, usa_dias_habiles = FALSE, "
        "    descripcion = 'R3 US-1.05: ETO sin plazo (indefinido)' "
        "WHERE tipo_tarea = 'LIBERACION'"
    )

    # ─── 6. CORRECCION: mismo SLA que REVISION (7/12/15) ───
    op.execute(
        "UPDATE semaforizacion_tarea "
        "SET dias_verde = 7, dias_amarillo = 12, dias_rojo = 15, "
        "    plazo_maximo_dias = 15, usa_dias_habiles = FALSE, "
        "    descripcion = 'R3 US-3.04: mismo SLA que REVISION (7/12/15)' "
        "WHERE tipo_tarea = 'CORRECCION'"
    )

    # ─── 7. Corregir server_default de la columna usa_dias_habiles ───
    # La migracion r3_fase1_s37 la creo con server_default=true.
    # La cambiamos a false para que nuevos INSERT usen FALSE.
    op.alter_column(
        "semaforizacion_tarea",
        "usa_dias_habiles",
        server_default=sa.text("false"),
    )


def downgrade() -> None:
    # Revertir: volver a los valores de la data migration r3_fase1_s37
    op.execute(
        "UPDATE semaforizacion_tarea "
        "SET dias_verde = 4, dias_amarillo = 7, dias_rojo = 10, "
        "    plazo_maximo_dias = 10, usa_dias_habiles = TRUE, "
        "    descripcion = 'R3 Fase 1: US-3.01 - 4/7/10 dias habiles' "
        "WHERE tipo_tarea IN ('REVISION', 'APROBACION')"
    )
    op.execute(
        "UPDATE semaforizacion_tarea "
        "SET usa_dias_habiles = TRUE, "
        "    descripcion = 'Verde 0-7, Amarillo 8-12, Rojo 13-15 (faltan 3 dias para cumplir plazo)' "
        "WHERE tipo_tarea = 'CONTROL_LECTURA'"
    )
    op.execute(
        "UPDATE semaforizacion_tarea "
        "SET usa_dias_habiles = TRUE, "
        "    descripcion = 'Verde 0-5, Amarillo 6-11, Rojo 12-15 (faltan 3 dias para cumplir plazo)' "
        "WHERE tipo_tarea = 'EVALUACION'"
    )
    op.execute(
        "UPDATE semaforizacion_tarea "
        "SET dias_verde = 4, dias_amarillo = 7, dias_rojo = 10, "
        "    plazo_maximo_dias = 10, usa_dias_habiles = TRUE, "
        "    descripcion = 'R3 Fase 1: US-1.05 ETO libera (mismo SLA que REVISION)' "
        "WHERE tipo_tarea = 'LIBERACION'"
    )
    op.execute(
        "UPDATE semaforizacion_tarea "
        "SET dias_verde = 4, dias_amarillo = 7, dias_rojo = 10, "
        "    plazo_maximo_dias = 10, usa_dias_habiles = TRUE, "
        "    descripcion = 'R3 Fase 1: US-3.04 elaborador corrige (mismo SLA que REVISION)' "
        "WHERE tipo_tarea = 'CORRECCION'"
    )
    op.alter_column(
        "semaforizacion_tarea",
        "usa_dias_habiles",
        server_default=sa.text("true"),
    )
