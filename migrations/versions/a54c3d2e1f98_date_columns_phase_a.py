"""Database schema migration for date columns phase A."""

from __future__ import annotations

import datetime as dt

from alembic import op
import sqlalchemy as sa
from sqlalchemy import exc as sa_exc

# revision identifiers, used by Alembic.
revision = 'a54c3d2e1f98'
down_revision = '0b1e4d5c6f70'
branch_labels = None
depends_on = None


def _get_columns(inspector, table_name: str) -> dict[str, dict]:
    return {col['name']: col for col in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Clean up leftovers from failed batch_alter_table runs on SQLite
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_company")
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_notes_receivable")

    company_cols = _get_columns(inspector, 'company')
    with op.batch_alter_table('company') as batch:
        if 'accounting_period_start_date' in company_cols:
            batch.alter_column(
                'accounting_period_start_date',
                new_column_name='accounting_period_start',
                existing_type=sa.Date(),
            )
        if 'accounting_period_end_date' in company_cols:
            batch.alter_column(
                'accounting_period_end_date',
                new_column_name='accounting_period_end',
                existing_type=sa.Date(),
            )
        if 'closing_date_date' in company_cols:
            batch.alter_column(
                'closing_date_date',
                new_column_name='closing_date',
                existing_type=sa.Date(),
            )

    inspector = sa.inspect(bind)
    note_cols = _get_columns(inspector, 'notes_receivable')
    issue_col = note_cols.get('issue_date')
    due_col = note_cols.get('due_date')

    with op.batch_alter_table('notes_receivable') as batch:
        if issue_col and isinstance(issue_col['type'], sa.String):
            batch.alter_column(
                'issue_date',
                new_column_name='issue_date_legacy',
                existing_type=sa.String(length=issue_col['type'].length or 10),
                existing_nullable=issue_col['nullable'],
                nullable=True,
            )
        elif 'issue_date_legacy' not in note_cols:
            batch.add_column(sa.Column('issue_date_legacy', sa.String(length=10), nullable=True))

        if due_col and isinstance(due_col['type'], sa.String):
            batch.alter_column(
                'due_date',
                new_column_name='due_date_legacy',
                existing_type=sa.String(length=due_col['type'].length or 10),
                existing_nullable=due_col['nullable'],
                nullable=True,
            )
        elif 'due_date_legacy' not in note_cols:
            batch.add_column(sa.Column('due_date_legacy', sa.String(length=10), nullable=True))

        if 'issue_date_date' in note_cols:
            batch.alter_column(
                'issue_date_date',
                new_column_name='issue_date',
                existing_type=sa.Date(),
            )
        if 'due_date_date' in note_cols:
            batch.alter_column(
                'due_date_date',
                new_column_name='due_date',
                existing_type=sa.Date(),
            )

    NOTES_RECEIVABLE = sa.table(
        'notes_receivable',
        sa.column('id', sa.Integer),
        sa.column('issue_date', sa.Date),
        sa.column('issue_date_legacy', sa.String(length=10)),
        sa.column('due_date', sa.Date),
        sa.column('due_date_legacy', sa.String(length=10)),
    )

    try:
        rows = bind.execute(
            sa.select(
                NOTES_RECEIVABLE.c.id,
                NOTES_RECEIVABLE.c.issue_date,
                NOTES_RECEIVABLE.c.issue_date_legacy,
                NOTES_RECEIVABLE.c.due_date,
                NOTES_RECEIVABLE.c.due_date_legacy,
            )
        ).mappings()
    except sa_exc.SQLAlchemyError:
        rows = []

    updates: list[tuple[int, dict[str, object]]] = []
    for row in rows:
        payload: dict[str, object] = {}
        if row.get('issue_date') is None and row.get('issue_date_legacy'):
            try:
                payload['issue_date'] = dt.date.fromisoformat(row['issue_date_legacy'])
            except ValueError:
                pass
        if row.get('due_date') is None and row.get('due_date_legacy'):
            try:
                payload['due_date'] = dt.date.fromisoformat(row['due_date_legacy'])
            except ValueError:
                pass
        if payload:
            updates.append((row['id'], payload))

    for pk, payload in updates:
        bind.execute(
            sa.update(NOTES_RECEIVABLE)
            .where(NOTES_RECEIVABLE.c.id == pk)
            .values(**payload)
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    op.execute("DROP TABLE IF EXISTS _alembic_tmp_company")
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_notes_receivable")

    note_cols = _get_columns(inspector, 'notes_receivable')
    if {'issue_date', 'issue_date_legacy', 'due_date', 'due_date_legacy'}.issubset(note_cols.keys()):
        rows = bind.execute(
            sa.select(
                sa.text('id'),
                sa.text('issue_date'),
                sa.text('due_date'),
            ).select_from(sa.text('notes_receivable'))
        ).mappings()
        for row in rows:
            payload: dict[str, object] = {}
            if row.get('issue_date'):
                payload['issue_date_legacy'] = row['issue_date']
            if row.get('due_date'):
                payload['due_date_legacy'] = row['due_date']
            if payload:
                bind.execute(
                    sa.text(
                        "UPDATE notes_receivable SET issue_date_legacy = :issue, due_date_legacy = :due WHERE id = :pk"
                    ),
                    {
                        'issue': payload.get('issue_date_legacy'),
                        'due': payload.get('due_date_legacy'),
                        'pk': row['id'],
                    },
                )

    inspector = sa.inspect(bind)
    note_cols = _get_columns(inspector, 'notes_receivable')
    with op.batch_alter_table('notes_receivable') as batch:
        if 'due_date' in note_cols and 'due_date_date' not in note_cols:
            batch.alter_column('due_date', new_column_name='due_date_date', existing_type=sa.Date())
        if 'issue_date' in note_cols and 'issue_date_date' not in note_cols:
            batch.alter_column('issue_date', new_column_name='issue_date_date', existing_type=sa.Date())
        if 'due_date_legacy' in note_cols:
            batch.alter_column(
                'due_date_legacy',
                new_column_name='due_date',
                existing_type=sa.String(length=10),
                nullable=True,
            )
        if 'issue_date_legacy' in note_cols:
            batch.alter_column(
                'issue_date_legacy',
                new_column_name='issue_date',
                existing_type=sa.String(length=10),
                nullable=True,
            )

    inspector = sa.inspect(bind)
    company_cols = _get_columns(inspector, 'company')
    with op.batch_alter_table('company') as batch:
        if 'closing_date' in company_cols and 'closing_date_date' not in company_cols:
            batch.alter_column('closing_date', new_column_name='closing_date_date', existing_type=sa.Date())
        if 'accounting_period_end' in company_cols and 'accounting_period_end_date' not in company_cols:
            batch.alter_column('accounting_period_end', new_column_name='accounting_period_end_date', existing_type=sa.Date())
        if 'accounting_period_start' in company_cols and 'accounting_period_start_date' not in company_cols:
            batch.alter_column('accounting_period_start', new_column_name='accounting_period_start_date', existing_type=sa.Date())
