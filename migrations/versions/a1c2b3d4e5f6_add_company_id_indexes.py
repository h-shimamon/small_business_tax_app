"""Database schema migration: add indexes on company_id across detail tables.

Revision ID: a1c2b3d4e5f6
Revises: 9c01e5a7aa10
Create Date: 2025-08-30 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1c2b3d4e5f6'
down_revision = '9c01e5a7aa10'
branch_labels = None
depends_on = None


TABLES = [
    'shareholder',
    'office',
    'deposit',
    'notes_receivable',
    'accounts_receivable',
    'temporary_payment',
    'loans_receivable',
    'inventory',
    'security',
    'fixed_asset',
    'notes_payable',
    'accounts_payable',
    'temporary_receipt',
    'borrowing',
    'executive_compensation',
    'land_rent',
    'miscellaneous',
    'accounting_data',  # already indexed in model; keep safe-check
]


def _has_index(inspector, table: str, name: str) -> bool:
    try:
        for ix in inspector.get_indexes(table):
            if ix.get('name') == name:
                return True
    except Exception:
        pass
    return False


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table in TABLES:
        idx_name = op.f(f"ix_{table}_company_id")
        if not _has_index(inspector, table, idx_name):
            op.create_index(idx_name, table, ['company_id'])


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table in TABLES:
        idx_name = op.f(f"ix_{table}_company_id")
        if _has_index(inspector, table, idx_name):
            op.drop_index(idx_name, table_name=table)
