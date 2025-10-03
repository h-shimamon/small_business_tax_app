"""Database schema migration: add constraints and columns to shareholder table.

Revision ID: 4d076bbb4efb
Revises: 71f6d8f1b56b
Create Date: 2025-08-13 12:06:07.427640
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d076bbb4efb'
down_revision = '71f6d8f1b56b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('shareholder', schema=None) as batch:
        batch.add_column(sa.Column('last_name', sa.String(length=50), nullable=False))
        batch.add_column(sa.Column('entity_type', sa.String(length=20), nullable=False, server_default='individual'))


def downgrade():
    with op.batch_alter_table('shareholder', schema=None) as batch:
        batch.drop_column('entity_type')
        batch.drop_column('last_name')
