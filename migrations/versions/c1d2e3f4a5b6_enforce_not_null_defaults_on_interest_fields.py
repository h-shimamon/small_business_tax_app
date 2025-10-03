"""Database schema migration: enforce non-null defaults on interest fields for loans and borrowings.

Revision ID: c1d2e3f4a5b6
Revises: a1c2b3d4e5f6
Create Date: 2025-08-30 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c1d2e3f4a5b6'
down_revision = 'a1c2b3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Backfill NULLs to 0 just in case (should be none per audit)
    op.execute(sa.text("UPDATE loans_receivable SET received_interest = 0 WHERE received_interest IS NULL"))
    op.execute(sa.text("UPDATE borrowing SET paid_interest = 0 WHERE paid_interest IS NULL"))

    with op.batch_alter_table('loans_receivable', schema=None) as batch_op:
        batch_op.alter_column('received_interest', existing_type=sa.Integer(), nullable=False, server_default='0')
    with op.batch_alter_table('borrowing', schema=None) as batch_op:
        batch_op.alter_column('paid_interest', existing_type=sa.Integer(), nullable=False, server_default='0')


def downgrade():
    with op.batch_alter_table('loans_receivable', schema=None) as batch_op:
        batch_op.alter_column('received_interest', existing_type=sa.Integer(), nullable=True, server_default=None)
    with op.batch_alter_table('borrowing', schema=None) as batch_op:
        batch_op.alter_column('paid_interest', existing_type=sa.Integer(), nullable=True, server_default=None)
