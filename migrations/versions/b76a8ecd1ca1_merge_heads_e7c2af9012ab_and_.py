"""Database schema migration: merge Alembic heads e7c2af9012ab and a6d2b1c34e12.

Revision ID: b76a8ecd1ca1
Revises: e7c2af9012ab, a6d2b1c34e12
Create Date: 2025-09-29 13:57:25.469990
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b76a8ecd1ca1'
down_revision = ('e7c2af9012ab', 'a6d2b1c34e12')
branch_labels = None
depends_on = None


def upgrade():
    # No-op merge migration to unify heads
    pass


def downgrade():
    # No-op; splitting heads is not supported automatically
    pass
