"""Merge heads 2b7d9e3f4a10 and 5b1a9f3c2d47

Revision ID: b2a8c6f5e3d1
Revises: 2b7d9e3f4a10, 5b1a9f3c2d47
Create Date: 2025-08-27 00:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2a8c6f5e3d1'
down_revision = ('2b7d9e3f4a10', '5b1a9f3c2d47')
branch_labels = None
depends_on = None


def upgrade():
    # No-op merge migration to unify heads
    pass


def downgrade():
    # No-op; splitting heads is not supported automatically
    pass
