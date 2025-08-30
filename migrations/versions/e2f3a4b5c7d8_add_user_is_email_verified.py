"""Add is_email_verified to user

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
    with op.batch_alter_table('user') as batch:
        batch.add_column(sa.Column('is_email_verified', sa.Boolean(), nullable=False, server_default=sa.text('0')))


def downgrade():
    with op.batch_alter_table('user') as batch:
        batch.drop_column('is_email_verified')
