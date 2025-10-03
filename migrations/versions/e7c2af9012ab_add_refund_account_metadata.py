"""Database schema migration.

Revision ID: e7c2af9012ab
Revises: 6e12ab34cd01
Create Date: 2025-08-23 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7c2af9012ab'
down_revision = '6e12ab34cd01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('company', schema=None) as batch_op:
        batch_op.add_column(sa.Column('refund_bank_type', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('refund_branch_type', sa.String(length=20), nullable=True))


def downgrade():
    with op.batch_alter_table('company', schema=None) as batch_op:
        batch_op.drop_column('refund_branch_type')
        batch_op.drop_column('refund_bank_type')
