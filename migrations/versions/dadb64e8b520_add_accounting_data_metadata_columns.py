"""Add accounting data metadata columns.

Revision ID: dadb64e8b520
Revises: b76a8ecd1ca1
Create Date: 2025-09-30 14:34:47.179714
"""
from alembic import op
import sqlalchemy as sa


revision = 'dadb64e8b520'
down_revision = 'b76a8ecd1ca1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('accounting_data', schema=None) as batch_op:
        batch_op.add_column(sa.Column('schema_version', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('algo_version', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('source_hash', sa.String(length=128), nullable=True))


def downgrade():
    with op.batch_alter_table('accounting_data', schema=None) as batch_op:
        batch_op.drop_column('schema_version')
        batch_op.drop_column('algo_version')
        batch_op.drop_column('source_hash')
