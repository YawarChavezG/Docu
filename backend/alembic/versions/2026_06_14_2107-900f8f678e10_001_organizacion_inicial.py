"""001_organizacion_inicial

Tablas: gerencias, areas, modulos, roles, usuarios, usuario_roles,
usuario_modulos, delegaciones, ausencias, firmas_digitales, log_sincronizacion_ad.

NOTA: el orden de creacion fue reordenado manualmente para resolver
dependencias circulares (areas <-> usuarios via jefe_id).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '900f8f678e10'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tablas sin dependencias (catálogos puros)
    op.create_table('gerencias',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sigla', sa.String(length=10), nullable=False),
    sa.Column('nombre', sa.String(length=150), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('orden', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gerencias_sigla'), 'gerencias', ['sigla'], unique=True)

    op.create_table('roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('codigo', sa.Enum('ADMIN', 'ETO', 'ELABORADOR - REVISOR', 'ELABORADOR - REVISOR - APROBADOR', 'VISUALIZADOR (CL-EVAL)', name='codigo_rol'), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('descripcion', sa.String(length=500), nullable=True),
    sa.Column('requiere_delegado', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('codigo')
    )

    op.create_table('modulos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('codigo', sa.Enum('BANDEJA_TAREAS', 'MI_BANDEJA', 'LISTA_MAESTRA', 'CONSULTAR_DOCUMENTOS', 'MIS_EVALUACIONES', 'ASISTENTE_IA', 'NUEVA_SOLICITUD', 'PLANTILLAS_DOCUMENTALES', 'PARAMETRIZACION', 'REPORTES', 'TODOS', name='codigo_modulo'), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('descripcion', sa.String(length=300), nullable=True),
    sa.Column('ruta_ui', sa.String(length=200), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('orden', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_modulos_codigo'), 'modulos', ['codigo'], unique=True)

    # 2. usuarios (sin FK a areas inicialmente; areas la referenciará después)
    op.create_table('usuarios',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('azure_oid', sa.String(length=100), nullable=True),
    sa.Column('email', sa.String(length=150), nullable=False),
    sa.Column('nombre_completo', sa.String(length=200), nullable=False),
    sa.Column('iniciales', sa.String(length=5), nullable=False),
    sa.Column('cargo', sa.String(length=100), nullable=False),
    sa.Column('area_id', sa.Integer(), nullable=True),
    sa.Column('estado', sa.Enum('activo', 'inactivo', 'desvinculado', 'ausente', name='estado_usuario'), nullable=False),
    sa.Column('ausente', sa.Boolean(), nullable=False),
    sa.Column('delegado_id', sa.Integer(), nullable=True),
    sa.Column('estado_delegacion', sa.Enum('pendiente', 'asignado', 'na', name='estado_delegacion'), nullable=False),
    sa.Column('visualiza_reportes', sa.Boolean(), nullable=False),
    sa.Column('requiere_delegado', sa.Boolean(), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=True),
    sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['delegado_id'], ['usuarios.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username', 'estado', name='uq_username_estado')
    )
    op.create_index(op.f('ix_usuarios_ausente'), 'usuarios', ['ausente'], unique=False)
    op.create_index(op.f('ix_usuarios_azure_oid'), 'usuarios', ['azure_oid'], unique=True)
    op.create_index(op.f('ix_usuarios_email'), 'usuarios', ['email'], unique=True)
    op.create_index(op.f('ix_usuarios_estado'), 'usuarios', ['estado'], unique=False)
    op.create_index(op.f('ix_usuarios_username'), 'usuarios', ['username'], unique=True)

    # 3. areas (depende de gerencias + usuarios para jefe_id)
    op.create_table('areas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('gerencia_id', sa.Integer(), nullable=False),
    sa.Column('sigla', sa.String(length=10), nullable=False),
    sa.Column('nombre', sa.String(length=150), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('jefe_id', sa.Integer(), nullable=True),
    sa.Column('orden', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['gerencia_id'], ['gerencias.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['jefe_id'], ['usuarios.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_areas_gerencia_id'), 'areas', ['gerencia_id'], unique=False)
    op.create_index(op.f('ix_areas_sigla'), 'areas', ['sigla'], unique=True)

    # 4. Ahora la FK area_id de usuarios puede existir
    op.create_index(op.f('ix_usuarios_area_id'), 'usuarios', ['area_id'], unique=False)
    op.create_foreign_key('fk_usuarios_area_id_areas', 'usuarios', 'areas',
                          ['area_id'], ['id'], ondelete='SET NULL')

    # 5. Tablas de soporte
    op.create_table('log_sincronizacion_ad',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tipo', sa.Enum('manual', 'automatico', name='tipo_sync_ad'), nullable=False),
    sa.Column('resultado', sa.Enum('exito', 'error', 'parcial', name='resultado_sync_ad'), nullable=False),
    sa.Column('triggered_by_user_id', sa.Integer(), nullable=True),
    sa.Column('usuarios_creados', sa.Integer(), nullable=False),
    sa.Column('usuarios_actualizados', sa.Integer(), nullable=False),
    sa.Column('usuarios_desvinculados', sa.Integer(), nullable=False),
    sa.Column('tareas_reasignadas', sa.Integer(), nullable=False),
    sa.Column('error_mensaje', sa.String(length=2000), nullable=True),
    sa.Column('duracion_ms', sa.Integer(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_log_sincronizacion_ad_resultado'), 'log_sincronizacion_ad', ['resultado'], unique=False)
    op.create_index(op.f('ix_log_sincronizacion_ad_tipo'), 'log_sincronizacion_ad', ['tipo'], unique=False)

    op.create_table('ausencias',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('fecha_desde', sa.Date(), nullable=False),
    sa.Column('fecha_hasta', sa.Date(), nullable=False),
    sa.Column('motivo', sa.String(length=50), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('notas', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ausencias_fecha_desde'), 'ausencias', ['fecha_desde'], unique=False)
    op.create_index(op.f('ix_ausencias_fecha_hasta'), 'ausencias', ['fecha_hasta'], unique=False)
    op.create_index(op.f('ix_ausencias_usuario_id'), 'ausencias', ['usuario_id'], unique=False)

    op.create_table('delegaciones',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('usuario_principal_id', sa.Integer(), nullable=False),
    sa.Column('delegado_id', sa.Integer(), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('notas', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['delegado_id'], ['usuarios.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['usuario_principal_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('usuario_principal_id', 'activo', name='uq_principal_activo')
    )
    op.create_index(op.f('ix_delegaciones_activo'), 'delegaciones', ['activo'], unique=False)
    op.create_index(op.f('ix_delegaciones_delegado_id'), 'delegaciones', ['delegado_id'], unique=False)
    op.create_index(op.f('ix_delegaciones_usuario_principal_id'), 'delegaciones', ['usuario_principal_id'], unique=False)

    op.create_table('firmas_digitales',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('accion', sa.String(length=50), nullable=False),
    sa.Column('recurso_tipo', sa.String(length=50), nullable=False),
    sa.Column('recurso_id', sa.Integer(), nullable=False),
    sa.Column('ip', sa.String(length=45), nullable=False),
    sa.Column('user_agent', sa.String(length=500), nullable=True),
    sa.Column('resultado_exito', sa.Boolean(), nullable=False),
    sa.Column('motivo_fallo', sa.String(length=200), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_firmas_digitales_accion'), 'firmas_digitales', ['accion'], unique=False)
    op.create_index(op.f('ix_firmas_digitales_recurso_id'), 'firmas_digitales', ['recurso_id'], unique=False)
    op.create_index(op.f('ix_firmas_digitales_resultado_exito'), 'firmas_digitales', ['resultado_exito'], unique=False)
    op.create_index(op.f('ix_firmas_digitales_usuario_id'), 'firmas_digitales', ['usuario_id'], unique=False)

    op.create_table('usuario_modulos',
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('modulo_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['modulo_id'], ['modulos.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('usuario_id', 'modulo_id')
    )

    op.create_table('usuario_roles',
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('rol_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['rol_id'], ['roles.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('usuario_id', 'rol_id')
    )


def downgrade() -> None:
    # Drop en orden inverso
    op.drop_table('usuario_roles')
    op.drop_table('usuario_modulos')
    op.drop_table('firmas_digitales')
    op.drop_table('delegaciones')
    op.drop_table('ausencias')
    op.drop_table('log_sincronizacion_ad')
    op.drop_foreign_key('fk_usuarios_area_id_areas', 'usuarios')
    op.drop_table('areas')
    op.drop_table('usuarios')
    op.drop_table('modulos')
    op.drop_table('roles')
    op.drop_table('gerencias')
