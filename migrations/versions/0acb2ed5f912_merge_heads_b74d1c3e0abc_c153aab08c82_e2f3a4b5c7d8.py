"""Database schema migration: merge Alembic heads b74d1c3e0abc, c153aab08c82, and e2f3a4b5c7d8.

Revision ID: 0acb2ed5f912
Revises: b74d1c3e0abc, c153aab08c82, e2f3a4b5c7d8
Create Date: 2025-10-31 00:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0acb2ed5f912'
down_revision = ('b74d1c3e0abc', 'c153aab08c82', 'e2f3a4b5c7d8')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op merge migration to unify divergent heads
    pass


def downgrade() -> None:
    # No-op; undoing a merge would require manual intervention
    pass
