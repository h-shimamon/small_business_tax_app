"""Database schema migration: add is_email_verified flag to user.

Revision ID: e2f3a4b5c7d8
Revises: d1e2f3a4b5c6
Create Date: 2025-08-30 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e2f3a4b5c7d8'
down_revision = 'd1e2f3a4b5c6'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col['name'] for col in inspector.get_columns('user')}
    if 'is_email_verified' in columns:
        return
    op.add_column(
        'user',
        sa.Column('is_email_verified', sa.Boolean(), nullable=False, server_default=sa.text('0')),
    )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col['name'] for col in inspector.get_columns('user')}
    if 'is_email_verified' not in columns:
        return
    if bind.dialect.name == 'sqlite':
        with op.batch_alter_table('user') as batch:
            batch.drop_column('is_email_verified')
    else:
        op.drop_column('user', 'is_email_verified')
