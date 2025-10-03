"""Database schema migration removing notes receivable legacy date columns."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b74d1c3e0abc'
down_revision = 'a54c3d2e1f98'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    legacy_columns = {col['name'] for col in inspector.get_columns('notes_receivable')}
    with op.batch_alter_table('notes_receivable') as batch:
        if 'issue_date_legacy' in legacy_columns:
            batch.drop_column('issue_date_legacy')
        if 'due_date_legacy' in legacy_columns:
            batch.drop_column('due_date_legacy')


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    current_columns = {col['name'] for col in inspector.get_columns('notes_receivable')}
    with op.batch_alter_table('notes_receivable') as batch:
        if 'issue_date_legacy' not in current_columns:
            batch.add_column(sa.Column('issue_date_legacy', sa.String(length=10), nullable=True))
        if 'due_date_legacy' not in current_columns:
            batch.add_column(sa.Column('due_date_legacy', sa.String(length=10), nullable=True))
