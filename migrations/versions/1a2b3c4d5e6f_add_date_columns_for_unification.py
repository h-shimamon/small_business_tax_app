"""add date columns for unification (parallel to String dates)

Revision ID: 1a2b3c4d5e6f
Revises: 91859660db66
Create Date: 2025-08-23
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = '91859660db66'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('company') as batch:
        batch.add_column(sa.Column('accounting_period_start_date', sa.Date(), nullable=True))
        batch.add_column(sa.Column('accounting_period_end_date', sa.Date(), nullable=True))
        batch.add_column(sa.Column('closing_date_date', sa.Date(), nullable=True))
    with op.batch_alter_table('notes_receivable') as batch:
        batch.add_column(sa.Column('issue_date_date', sa.Date(), nullable=True))
        batch.add_column(sa.Column('due_date_date', sa.Date(), nullable=True))


def downgrade():
    with op.batch_alter_table('notes_receivable') as batch:
        batch.drop_column('due_date_date')
        batch.drop_column('issue_date_date')
    with op.batch_alter_table('company') as batch:
        batch.drop_column('closing_date_date')
        batch.drop_column('accounting_period_end_date')
        batch.drop_column('accounting_period_start_date')

