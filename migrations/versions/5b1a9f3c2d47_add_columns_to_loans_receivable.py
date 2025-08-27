"""Add columns to LoansReceivable: registration_number, relationship, collateral_details

Revision ID: 5b1a9f3c2d47
Revises: c48f2abe8868
Create Date: 2025-08-27 00:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5b1a9f3c2d47'
down_revision = 'c48f2abe8868'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('loans_receivable') as batch:
        batch.add_column(sa.Column('registration_number', sa.String(length=20), nullable=True))
        batch.add_column(sa.Column('relationship', sa.String(length=100), nullable=True))
        batch.add_column(sa.Column('collateral_details', sa.String(length=200), nullable=True))


def downgrade():
    with op.batch_alter_table('loans_receivable') as batch:
        batch.drop_column('collateral_details')
        batch.drop_column('relationship')
        batch.drop_column('registration_number')
