"""backfill string dates to new Date columns

Revision ID: 2b7d9e3f4a10
Revises: 1a5fbe21e62c
Create Date: 2025-08-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import String, Date, Integer
import datetime as dt

# revision identifiers, used by Alembic.
revision = '2b7d9e3f4a10'
down_revision = '1a5fbe21e62c'
branch_labels = None
depends_on = None


def _to_date(value):
    if not value:
        return None
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(value)
    except Exception:
        return None


def upgrade():
    bind = op.get_bind()
    metadata = sa.MetaData(bind=bind)

    company = sa.Table(
        'company', metadata,
        sa.Column('id', Integer),
        sa.Column('accounting_period_start', String(10)),
        sa.Column('accounting_period_start_date', Date),
        sa.Column('accounting_period_end', String(10)),
        sa.Column('accounting_period_end_date', Date),
        sa.Column('closing_date', String(10)),
        sa.Column('closing_date_date', Date),
    )
    notes = sa.Table(
        'notes_receivable', metadata,
        sa.Column('id', Integer),
        sa.Column('issue_date', String(10)),
        sa.Column('issue_date_date', Date),
        sa.Column('due_date', String(10)),
        sa.Column('due_date_date', Date),
    )

    # Backfill company dates
    res = bind.execute(sa.select(company.c.id, company.c.accounting_period_start, company.c.accounting_period_end, company.c.closing_date))
    for rid, s_start, s_end, s_close in res.fetchall():
        vals = {}
        d = _to_date(s_start)
        if d is not None:
            vals['accounting_period_start_date'] = d
        d = _to_date(s_end)
        if d is not None:
            vals['accounting_period_end_date'] = d
        d = _to_date(s_close)
        if d is not None:
            vals['closing_date_date'] = d
        if vals:
            bind.execute(company.update().where(company.c.id == rid).values(**vals))

    # Backfill notes_receivable dates
    res = bind.execute(sa.select(notes.c.id, notes.c.issue_date, notes.c.due_date))
    for rid, s_issue, s_due in res.fetchall():
        vals = {}
        d = _to_date(s_issue)
        if d is not None:
            vals['issue_date_date'] = d
        d = _to_date(s_due)
        if d is not None:
            vals['due_date_date'] = d
        if vals:
            bind.execute(notes.update().where(notes.c.id == rid).values(**vals))


def downgrade():
    # Non-destructive: clear backfilled Date columns (optional)
    bind = op.get_bind()
    metadata = sa.MetaData(bind=bind)
    company = sa.Table('company', metadata,
                       sa.Column('id', Integer),
                       sa.Column('accounting_period_start_date', Date),
                       sa.Column('accounting_period_end_date', Date),
                       sa.Column('closing_date_date', Date))
    notes = sa.Table('notes_receivable', metadata,
                     sa.Column('id', Integer),
                     sa.Column('issue_date_date', Date),
                     sa.Column('due_date_date', Date))
    bind.execute(company.update().values(
        accounting_period_start_date=None,
        accounting_period_end_date=None,
        closing_date_date=None,
    ))
    bind.execute(notes.update().values(
        issue_date_date=None,
        due_date_date=None,
    ))

