"""refactor tipos_documento: codigo int + slug + nombre unique

REFACTOR sesion 13 (2026-06-16):
  Antes:
    - `codigo` (str slug, ej: 'PROCEDIMIENTO')  -- unico
    - `codigo_doc` (int, 1-14)                  -- NO unico
    - `nombre` (str)

  Despues:
    - `codigo` (int, 1-14)   -- UNIQUE
    - `slug` (str MAYUSCULAS) -- UNIQUE (lo que antes era `codigo`)
    - `nombre` (str)         -- UNIQUE
    - DROP `codigo_doc` (redundante con `codigo`)

Revision ID: 6b244889632f
Revises: b397cd9bfb91
Create Date: 2026-06-16 23:48:52.480875

NOTA sobre data migration:
  El codigo viejo (string slug) se preserva en una columna temporal
  `__old_codigo` agregada al inicio, para poder copiarla a `slug`
  despues de DROP+RENAME de codigo.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b244889632f'
down_revision: Union[str, None] = 'b397cd9bfb91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── 1. Backup: copiar codigo viejo (string) a columna temporal ───
    op.add_column('tipos_documento', sa.Column('__old_codigo', sa.String(length=50), nullable=True))
    op.execute("UPDATE tipos_documento SET __old_codigo = codigo")

    # ─── 2. Eliminar UNIQUE constraint de codigo (string) y INDEX de codigo_doc ───
    op.execute("""
        DO $$
        DECLARE
            cons_name text;
        BEGIN
            SELECT conname INTO cons_name
            FROM pg_constraint
            WHERE conrelid = 'tipos_documento'::regclass
              AND contype = 'u'
              AND pg_get_constraintdef(oid) LIKE '%(codigo)%';
            IF cons_name IS NOT NULL THEN
                EXECUTE format('ALTER TABLE tipos_documento DROP CONSTRAINT %I', cons_name);
            END IF;
        END $$;
    """)
    op.drop_index('ix_tipos_documento_codigo_doc', table_name='tipos_documento', if_exists=True)

    # ─── 3. DROP columna codigo (string) ───
    op.drop_column('tipos_documento', 'codigo')

    # ─── 4. RENAME codigo_doc -> codigo ───
    op.alter_column('tipos_documento', 'codigo_doc', new_column_name='codigo')

    # ─── 5. ADD slug (nullable) y copiar desde __old_codigo ───
    op.add_column('tipos_documento', sa.Column('slug', sa.String(length=50), nullable=True))
    op.execute("UPDATE tipos_documento SET slug = __old_codigo")

    # ─── 6. DROP columna temporal ───
    op.drop_column('tipos_documento', '__old_codigo')

    # ─── 6.5. Resolver duplicados de codigo: INSTRUCTIVO e INSTRUCTIVO_TECNICO
    # ambos tenian codigo_doc=6. Como el nuevo `codigo` debe ser UNIQUE,
    # reasignamos INSTRUCTIVO_TECNICO a 15 (siguiente libre, >14).
    op.execute("UPDATE tipos_documento SET codigo = 15 WHERE slug = 'INSTRUCTIVO_TECNICO'")

    # ─── 7. Hacer NOT NULL y crear constraints nuevos ───
    op.alter_column('tipos_documento', 'slug', nullable=False)
    op.create_index(
        op.f('ix_tipos_documento_slug'),
        'tipos_documento', ['slug'], unique=True,
    )
    op.create_unique_constraint('uq_tipos_documento_codigo', 'tipos_documento', ['codigo'])
    op.create_unique_constraint('uq_tipos_documento_nombre', 'tipos_documento', ['nombre'])


def downgrade() -> None:
    op.drop_constraint('uq_tipos_documento_nombre', 'tipos_documento', type_='unique')
    op.drop_constraint('uq_tipos_documento_codigo', 'tipos_documento', type_='unique')
    op.drop_index(op.f('ix_tipos_documento_slug'), table_name='tipos_documento')

    # Restaurar: backup slug en temporal
    op.add_column('tipos_documento', sa.Column('__old_slug', sa.String(length=50), nullable=True))
    op.execute("UPDATE tipos_documento SET __old_slug = slug")

    op.alter_column('tipos_documento', 'slug', nullable=True)
    op.drop_column('tipos_documento', 'slug')
    op.alter_column('tipos_documento', 'codigo', new_column_name='codigo_doc')

    op.add_column('tipos_documento', sa.Column('codigo', sa.String(length=50), nullable=True))
    op.execute("UPDATE tipos_documento SET codigo = __old_slug")
    op.alter_column('tipos_documento', 'codigo', nullable=False)
    op.drop_column('tipos_documento', '__old_slug')

    op.create_unique_constraint(
        op.f('uq_tipos_documento_codigo'), 'tipos_documento', ['codigo'],
    )
    op.create_index(
        op.f('ix_tipos_documento_codigo_doc'),
        'tipos_documento', ['codigo_doc'], unique=False,
    )
