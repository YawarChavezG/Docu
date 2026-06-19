"""R3 Fase 1 (sesion 37): crear 7 tablas nuevas + extender enum + semaforo

Crea las 7 tablas del workflow de revision y aprobacion (PROPUESTA-R3-TABLAS.md):

1. `procesos` - catalogo para `documentos.proceso_id` (sin FK actualmente).
2. `tareas` - pieza central del workflow. Reemplaza JSONB `revisor_ids` /
   `aprobador_ids` de `documento_flujo` por tabla N:M con estado individual
   por tarea, SLA y reasignacion trazable (US-3.01, US-3.06, US-3.04).
3. `bitacora_timeline` - timeline inmutable del documento (US-8.01).
   Append-only. CHECK constraint en color_nodo.
4. `notificaciones` - cola persistente de notificaciones con tracking de
   lectura + email_enviado. Reemplaza el polling del store frontend.
5. `documento_reemplazos` - N:M para reemplazos. Reemplaza JSONB
   `reemplaza_documento_ids` de `documento_flujo` (US-1.07, US-5.01).
6. `documento_alcance_difusion` - N:M para difusion. Reemplaza JSONB
   `alcance_difusion_ids` de `documento_flujo` (US-1.06).
7. `tarea_observaciones` - observaciones por tarea. CHECK min 10 chars
   (US-3.04).

Ademas:
- ALTER TYPE tipo_tarea_semaforo ADD VALUE 'LIBERACION', 'CORRECCION'
  (US-1.05, US-3.04). PG < 12 no soporta DROP VALUE, downgrade vacio
  intencional (mismo patron que `r3_liberacion_eto_s36`).
- ALTER TABLE semaforizacion_tarea ADD COLUMN usa_dias_habiles BOOLEAN
  (US-3.01: el plazo es en dias HABILES, no naturales).
- Data migration: UPDATE semaforizacion_tarea SET dias_verde=4, amarillo=7,
  rojo=10, plazo_maximo=10 para REVISION/APROBACION segun US-3.01.
  Tambien: crear filas LIBERACION y CORRECCION con valores heredados
  de REVISION (mismo SLA).

Revision ID: r3_fase1_s37
Revises: 674e063e672b
Create Date: 2026-06-19 12:38:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "r3_fase1_s37"
down_revision: Union[str, None] = "674e063e672b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── 1. Extender enum tipo_tarea_semaforo (PG: requiere autocommit) ───
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE tipo_tarea_semaforo ADD VALUE IF NOT EXISTS 'LIBERACION'"
        )
        op.execute(
            "ALTER TYPE tipo_tarea_semaforo ADD VALUE IF NOT EXISTS 'CORRECCION'"
        )

    # ─── 2. Columna usa_dias_habiles en semaforizacion_tarea ───
    # Default TRUE (US-3.01: el plazo es en dias habiles).
    op.add_column(
        "semaforizacion_tarea",
        sa.Column(
            "usa_dias_habiles",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    # ─── 3. Tabla procesos (catalogo) ───
    op.create_table(
        "procesos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("descripcion", sa.String(length=500), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre", name="uq_procesos_nombre"),
    )

    # ─── 4. Tabla tareas (N:M pieza central) ───
    op.create_table(
        "tareas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("documento_flujo_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("delegado_origen_id", sa.Integer(), nullable=True),
        sa.Column(
            "tipo_tarea",
            sa.Enum(
                "REVISION", "APROBACION", "CONTROL_LECTURA", "EVALUACION",
                "LIBERACION", "CORRECCION",
                name="tipo_tarea_semaforo",
            ),
            nullable=False,
        ),
        sa.Column("firma_id", sa.Integer(), nullable=True),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="PENDIENTE"),
        sa.Column("fecha_asignacion", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("fecha_vencimiento", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_completado", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_limite_eval", sa.DateTime(timezone=True), nullable=True),
        sa.Column("intento_reasignacion", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("observacion", sa.Text(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "estado IN ('PENDIENTE', 'COMPLETADO', 'RECHAZADO', "
            "'REASIGNADO', 'VENCIDO', 'NO_EJECUTADO')",
            name="ck_tarea_estado_valido",
        ),
        sa.CheckConstraint(
            "intento_reasignacion >= 0 AND intento_reasignacion <= 3",
            name="ck_tarea_intento_rango",
        ),
        sa.ForeignKeyConstraint(["delegado_origen_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["documento_flujo_id"], ["documento_flujo.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["firma_id"], ["firmas_digitales.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tipo_tarea"], ["semaforizacion_tarea.tipo_tarea"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "documento_flujo_id", "usuario_id", "tipo_tarea", "fecha_asignacion",
            name="uq_tarea_flujo_usuario_tipo_fecha",
        ),
    )
    op.create_index(
        "ix_tareas_usuario_estado", "tareas",
        ["usuario_id", "estado"],
        postgresql_where=sa.text("activo = TRUE"),
    )
    op.create_index(
        "ix_tareas_flujo_tipo", "tareas",
        ["documento_flujo_id", "tipo_tarea"],
    )
    op.create_index(
        "ix_tareas_vencimiento", "tareas",
        ["fecha_vencimiento"],
        postgresql_where=sa.text("estado = 'PENDIENTE'"),
    )
    op.create_index(
        "ix_tareas_asignacion", "tareas",
        ["fecha_asignacion"],
        postgresql_where=sa.text("estado = 'PENDIENTE'"),
    )

    # ─── 5. Tabla bitacora_timeline (append-only) ───
    op.create_table(
        "bitacora_timeline",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("documento_flujo_id", sa.Integer(), nullable=False),
        sa.Column("tarea_id", sa.Integer(), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("accion", sa.String(length=50), nullable=False),
        sa.Column("estado_origen", sa.String(length=50), nullable=True),
        sa.Column("estado_destino", sa.String(length=50), nullable=True),
        sa.Column("color_nodo", sa.String(length=10), nullable=False, server_default="azul"),
        sa.Column("observacion", sa.Text(), nullable=True),
        sa.Column("adjunto_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "color_nodo IN ('azul', 'verde', 'rojo', 'ambar', 'gris')",
            name="ck_bitacora_color_valido",
        ),
        sa.ForeignKeyConstraint(["documento_flujo_id"], ["documento_flujo.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tarea_id"], ["tareas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bitacora_flujo", "bitacora_timeline", ["documento_flujo_id", "created_at"])
    op.create_index("ix_bitacora_usuario", "bitacora_timeline", ["usuario_id"])
    op.create_index("ix_bitacora_accion_fecha", "bitacora_timeline", ["accion", "created_at"])

    # ─── 6. Tabla notificaciones (cola persistente) ───
    op.create_table(
        "notificaciones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_destino_id", sa.Integer(), nullable=False),
        sa.Column("usuario_origen_id", sa.Integer(), nullable=True),
        sa.Column("documento_flujo_id", sa.Integer(), nullable=True),
        sa.Column("tarea_id", sa.Integer(), nullable=True),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("tipo_notificacion", sa.String(length=30), nullable=False),
        sa.Column("leida", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("fecha_lectura", sa.DateTime(timezone=True), nullable=True),
        sa.Column("leida_en", sa.String(length=45), nullable=True),
        sa.Column("email_enviado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("email_enviado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "tipo_notificacion IN ("
            "'ASIGNACION_TAREA', 'REASIGNACION', 'VENCIMIENTO', "
            "'DEVOLUCION', 'CORRECCION', 'PUBLICACION', "
            "'CONTROL_LECTURA', 'EVALUACION', 'SISTEMA'"
            ")",
            name="ck_notif_tipo_valido",
        ),
        sa.ForeignKeyConstraint(["documento_flujo_id"], ["documento_flujo.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tarea_id"], ["tareas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["usuario_destino_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_origen_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notif_usuario_no_leidas", "notificaciones",
        ["usuario_destino_id", "leida"],
        postgresql_where=sa.text("leida = FALSE"),
    )
    op.create_index(
        "ix_notif_usuario_fecha", "notificaciones",
        ["usuario_destino_id", "created_at"],
    )
    op.create_index("ix_notif_flujo", "notificaciones", ["documento_flujo_id"])

    # ─── 7. Tabla documento_reemplazos (N:M reemplazos) ───
    op.create_table(
        "documento_reemplazos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("documento_flujo_id", sa.Integer(), nullable=False),
        sa.Column("documento_viejo_id", sa.Integer(), nullable=True),
        sa.Column("codigo_documento_viejo", sa.String(length=20), nullable=False),
        sa.Column("ejecutado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("ejecutado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["documento_flujo_id"], ["documento_flujo.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["documento_viejo_id"], ["documentos.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reemplazos_flujo", "documento_reemplazos", ["documento_flujo_id"])
    op.create_index("ix_reemplazos_codigo", "documento_reemplazos", ["codigo_documento_viejo"])
    op.create_index(
        "ix_reemplazos_pendientes", "documento_reemplazos",
        ["documento_viejo_id"],
        postgresql_where=sa.text("ejecutado = FALSE AND documento_viejo_id IS NOT NULL"),
    )

    # ─── 8. Tabla documento_alcance_difusion (N:M difusion) ───
    op.create_table(
        "documento_alcance_difusion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("documento_flujo_id", sa.Integer(), nullable=False),
        sa.Column("gerencia_id", sa.Integer(), nullable=True),
        sa.Column("area_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "(gerencia_id IS NOT NULL AND area_id IS NULL) OR "
            "(gerencia_id IS NULL AND area_id IS NOT NULL)",
            name="ck_alcance_exactly_one",
        ),
        sa.ForeignKeyConstraint(["area_id"], ["areas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["documento_flujo_id"], ["documento_flujo.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["gerencia_id"], ["gerencias.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alcance_flujo", "documento_alcance_difusion", ["documento_flujo_id"])

    # ─── 9. Tabla tarea_observaciones ───
    op.create_table(
        "tarea_observaciones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tarea_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("observacion", sa.Text(), nullable=False),
        sa.Column("corregida", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("corregida_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("length(observacion) >= 10", name="ck_observacion_min_10_chars"),
        sa.ForeignKeyConstraint(["tarea_id"], ["tareas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_obs_tarea", "tarea_observaciones", ["tarea_id"])
    op.create_index(
        "ix_obs_pendientes", "tarea_observaciones",
        ["tarea_id", "corregida"],
        postgresql_where=sa.text("corregida = FALSE"),
    )

    # ─── 10. Data migration: valores de semaforo segun US-3.01 ───
    # REVISION y APROBACION: verde=4, amarillo=7, rojo=10, plazo=10 (dias habiles).
    # CONTROL_LECTURA y EVALUACION: mantienen 7/12/15 y 5/11/15 (legacy R1, dias naturales).
    op.execute(
        "UPDATE semaforizacion_tarea "
        "SET dias_verde = 4, dias_amarillo = 7, dias_rojo = 10, "
        "    plazo_maximo_dias = 10, usa_dias_habiles = TRUE, "
        "    descripcion = 'R3 Fase 1: US-3.01 - 4/7/10 dias habiles' "
        "WHERE tipo_tarea IN ('REVISION', 'APROBACION')"
    )

    # Crear filas LIBERACION y CORRECCION con valores heredados de REVISION.
    # (Ya hicimos ALTER TYPE ADD VALUE arriba; ahora insertamos las filas).
    op.execute(
        "INSERT INTO semaforizacion_tarea "
        "(tipo_tarea, dias_verde, dias_amarillo, dias_rojo, plazo_maximo_dias, "
        " usa_dias_habiles, descripcion, activo) "
        "VALUES "
        "('LIBERACION', 4, 7, 10, 10, TRUE, "
        " 'R3 Fase 1: US-1.05 ETO libera (mismo SLA que REVISION)', TRUE), "
        "('CORRECCION', 4, 7, 10, 10, TRUE, "
        " 'R3 Fase 1: US-3.04 elaborador corrige (mismo SLA que REVISION)', TRUE) "
        "ON CONFLICT (tipo_tarea) DO NOTHING"
    )


def downgrade() -> None:
    # ─── 1. Drop tablas en orden inverso (respetando FKs) ───
    op.drop_index("ix_obs_pendientes", table_name="tarea_observaciones")
    op.drop_index("ix_obs_tarea", table_name="tarea_observaciones")
    op.drop_table("tarea_observaciones")

    op.drop_index("ix_alcance_flujo", table_name="documento_alcance_difusion")
    op.drop_table("documento_alcance_difusion")

    op.drop_index("ix_reemplazos_pendientes", table_name="documento_reemplazos")
    op.drop_index("ix_reemplazos_codigo", table_name="documento_reemplazos")
    op.drop_index("ix_reemplazos_flujo", table_name="documento_reemplazos")
    op.drop_table("documento_reemplazos")

    op.drop_index("ix_notif_flujo", table_name="notificaciones")
    op.drop_index("ix_notif_usuario_fecha", table_name="notificaciones")
    op.drop_index("ix_notif_usuario_no_leidas", table_name="notificaciones")
    op.drop_table("notificaciones")

    op.drop_index("ix_bitacora_accion_fecha", table_name="bitacora_timeline")
    op.drop_index("ix_bitacora_usuario", table_name="bitacora_timeline")
    op.drop_index("ix_bitacora_flujo", table_name="bitacora_timeline")
    op.drop_table("bitacora_timeline")

    op.drop_index("ix_tareas_asignacion", table_name="tareas")
    op.drop_index("ix_tareas_vencimiento", table_name="tareas")
    op.drop_index("ix_tareas_flujo_tipo", table_name="tareas")
    op.drop_index("ix_tareas_usuario_estado", table_name="tareas")
    op.drop_table("tareas")

    op.drop_table("procesos")

    # ─── 2. Revertir data migration de semaforo (a valores legacy) ───
    op.execute(
        "DELETE FROM semaforizacion_tarea "
        "WHERE tipo_tarea IN ('LIBERACION', 'CORRECCION')"
    )
    op.execute(
        "UPDATE semaforizacion_tarea "
        "SET dias_verde = 7, dias_amarillo = 12, dias_rojo = 15, "
        "    plazo_maximo_dias = 15, usa_dias_habiles = FALSE "
        "WHERE tipo_tarea IN ('REVISION', 'APROBACION')"
    )

    # ─── 3. Drop columna usa_dias_habiles ───
    op.drop_column("semaforizacion_tarea", "usa_dias_habiles")

    # ─── 4. Enum: PG < 12 no soporta DROP VALUE. No revertir. ───
    # Documentado en DECISIONES.md (mismo patron que `r3_liberacion_eto_s36`).
    pass
