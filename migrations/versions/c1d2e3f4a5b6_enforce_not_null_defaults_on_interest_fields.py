"""Enforce NOT NULL + DEFAULT 0 on interest-related fields

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

    # Apply NOT NULL + DEFAULT 0 (SQLite-safe via batch)
    with op.batch_alter_table('loans_receivable') as batch:
        batch.alter_column(
            'received_interest',
            existing_type=sa.Integer(),
            server_default=sa.text('0'),
            nullable=False,
        )
    with op.batch_alter_table('borrowing') as batch:
        batch.alter_column(
            'paid_interest',
            existing_type=sa.Integer(),
            server_default=sa.text('0'),
            nullable=False,
        )


def downgrade():
    # Revert to nullable and drop server defaults
    with op.batch_alter_table('loans_receivable') as batch:
        batch.alter_column(
            'received_interest',
            existing_type=sa.Integer(),
            server_default=None,
            nullable=True,
        )
    with op.batch_alter_table('borrowing') as batch:
        batch.alter_column(
            'paid_interest',
            existing_type=sa.Integer(),
            server_default=None,
            nullable=True,
        )
