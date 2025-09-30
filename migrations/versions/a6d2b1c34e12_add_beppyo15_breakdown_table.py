"""add beppyo15 breakdown table

Revision ID: a6d2b1c34e12
Revises: 7faaf5f3a9e9
Create Date: 2025-09-10 12:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6d2b1c34e12'
down_revision = ('7faaf5f3a9e9', 'c153aab08c82')
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'beppyo15_breakdown',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(length=100), nullable=False),
        sa.Column('expense_amount', sa.Integer(), nullable=False),
        sa.Column('deductible_amount', sa.Integer(), nullable=False),
        sa.Column('net_amount', sa.Integer(), nullable=False),
        sa.Column('hospitality_amount', sa.Integer(), nullable=False),
        sa.Column('remarks', sa.String(length=200), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['company.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_beppyo15_breakdown_company_id'), 'beppyo15_breakdown', ['company_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_beppyo15_breakdown_company_id'), table_name='beppyo15_breakdown')
    op.drop_table('beppyo15_breakdown')
