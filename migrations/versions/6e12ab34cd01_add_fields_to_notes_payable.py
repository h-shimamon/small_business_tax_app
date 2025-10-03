"""Database schema migration: add registration and payment fields to notes_payable.

Revision ID: 6e12ab34cd01
Revises: f4f5494df524
Create Date: 2025-08-27 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '6e12ab34cd01'
down_revision = 'f4f5494df524'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('notes_payable') as batch:
        batch.add_column(sa.Column('registration_number', sa.String(length=20), nullable=True))
        batch.add_column(sa.Column('payer_bank', sa.String(length=100), nullable=True))
        batch.add_column(sa.Column('payer_branch', sa.String(length=100), nullable=True))


def downgrade():
    with op.batch_alter_table('notes_payable') as batch:
        batch.drop_column('payer_branch')
        batch.drop_column('payer_bank')
        batch.drop_column('registration_number')
