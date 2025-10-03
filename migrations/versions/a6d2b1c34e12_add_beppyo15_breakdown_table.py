"""Database schema migration: add beppyo15 breakdown table.

Revision ID: a6d2b1c34e12
Revises: 7faaf5f3a9e9
Create Date: 2025-08-27 22:20:41.019441
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6d2b1c34e12'
down_revision = '7faaf5f3a9e9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'beppyo15_breakdown',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('account_name', sa.String(length=100), nullable=False),
        sa.Column('expense_amount', sa.Integer(), nullable=False),
        sa.Column('deductible_amount', sa.Integer(), nullable=False),
        sa.Column('net_amount', sa.Integer(), nullable=False),
        sa.Column('hospitality_amount', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_beppyo15_breakdown_company_id'), 'beppyo15_breakdown', ['company_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_beppyo15_breakdown_company_id'), table_name='beppyo15_breakdown')
    op.drop_table('beppyo15_breakdown')
