"""Database schema migration: add registration_number to accounts_payable.

Revision ID: 9c01e5a7aa10
Revises: 7faaf5f3a9e9
Create Date: 2025-08-27 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9c01e5a7aa10'
down_revision = '7faaf5f3a9e9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('accounts_payable') as batch:
        batch.add_column(sa.Column('registration_number', sa.String(length=20), nullable=True))


def downgrade():
    with op.batch_alter_table('accounts_payable') as batch:
        batch.drop_column('registration_number')
