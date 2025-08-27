"""merge heads: notes_payable fields

Revision ID: 7faaf5f3a9e9
Revises: 6e12ab34cd01, b2a8c6f5e3d1
Create Date: 2025-08-27 22:18:54.619664

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7faaf5f3a9e9'
down_revision = ('6e12ab34cd01', 'b2a8c6f5e3d1')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
