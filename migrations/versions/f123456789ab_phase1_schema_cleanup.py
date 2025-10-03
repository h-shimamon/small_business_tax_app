"""Database schema migration for phase 1 schema cleanup."""

"""Phase1 schema cleanup: unify exclusion flag and accounting dates."""

from __future__ import annotations

from datetime import date, datetime

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f123456789ab'
down_revision = 'dadb64e8b520'
branch_labels = None
depends_on = None

LEGACY_COMPANY = sa.table(
    'company',
    sa.column('id', sa.Integer),
    sa.column('accounting_period_start', sa.String(length=10)),
    sa.column('accounting_period_end', sa.String(length=10)),
    sa.column('closing_date', sa.String(length=10)),
    sa.column('accounting_period_start_date', sa.Date),
    sa.column('accounting_period_end_date', sa.Date),
    sa.column('closing_date_date', sa.Date),
    sa.column('is_not_excluded_business', sa.Boolean),
    sa.column('is_excluded_business', sa.Boolean),
)

CURRENT_COMPANY = sa.table(
    'company',
    sa.column('id', sa.Integer),
    sa.column('accounting_period_start_date', sa.Date),
    sa.column('accounting_period_end_date', sa.Date),
    sa.column('closing_date_date', sa.Date),
    sa.column('is_excluded_business', sa.Boolean),
    sa.column('accounting_period_start', sa.String(length=10)),
    sa.column('accounting_period_end', sa.String(length=10)),
    sa.column('closing_date', sa.String(length=10)),
    sa.column('is_not_excluded_business', sa.Boolean),
)


def _parse_iso_date(value) -> date | None:
    if value in (None, ''):
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except Exception:
        return None


def _iso_or_none(value) -> str | None:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, datetime):  # defensive: timestamp columns
        return value.date().isoformat()
    return None


def upgrade() -> None:
    bind = op.get_bind()

    # Backfill date columns from legacy string columns and reconcile exclusion flag.
    rows = bind.execute(
        sa.select(
            LEGACY_COMPANY.c.id,
            LEGACY_COMPANY.c.accounting_period_start,
            LEGACY_COMPANY.c.accounting_period_start_date,
            LEGACY_COMPANY.c.accounting_period_end,
            LEGACY_COMPANY.c.accounting_period_end_date,
            LEGACY_COMPANY.c.closing_date,
            LEGACY_COMPANY.c.closing_date_date,
            LEGACY_COMPANY.c.is_not_excluded_business,
        )
    ).mappings()

    for row in rows:
        updates: dict[str, object] = {}

        aps = _parse_iso_date(row['accounting_period_start'])
        if aps is not None:
            updates['accounting_period_start_date'] = aps
        ape = _parse_iso_date(row['accounting_period_end'])
        if ape is not None:
            updates['accounting_period_end_date'] = ape
        clo = _parse_iso_date(row['closing_date'])
        if clo is not None:
            updates['closing_date_date'] = clo

        flag = row['is_not_excluded_business']
        if flag is not None:
            updates['is_excluded_business'] = not bool(flag)

        if updates:
            bind.execute(
                sa.update(CURRENT_COMPANY)
                .where(CURRENT_COMPANY.c.id == row['id'])
                .values(**updates)
            )

    with op.batch_alter_table('company') as batch:
        batch.drop_column('accounting_period_start')
        batch.drop_column('accounting_period_end')
        batch.drop_column('closing_date')
        batch.drop_column('is_not_excluded_business')


def downgrade() -> None:
    with op.batch_alter_table('company') as batch:
        batch.add_column(sa.Column('is_not_excluded_business', sa.Boolean(), nullable=True))
        batch.add_column(sa.Column('closing_date', sa.String(length=10), nullable=True))
        batch.add_column(sa.Column('accounting_period_end', sa.String(length=10), nullable=True))
        batch.add_column(sa.Column('accounting_period_start', sa.String(length=10), nullable=True))

    bind = op.get_bind()

    rows = bind.execute(
        sa.select(
            CURRENT_COMPANY.c.id,
            CURRENT_COMPANY.c.accounting_period_start_date,
            CURRENT_COMPANY.c.accounting_period_end_date,
            CURRENT_COMPANY.c.closing_date_date,
            CURRENT_COMPANY.c.is_excluded_business,
        )
    ).mappings()

    for row in rows:
        updates: dict[str, object] = {}
        aps = _iso_or_none(row['accounting_period_start_date'])
        if aps is not None:
            updates['accounting_period_start'] = aps
        ape = _iso_or_none(row['accounting_period_end_date'])
        if ape is not None:
            updates['accounting_period_end'] = ape
        clo = _iso_or_none(row['closing_date_date'])
        if clo is not None:
            updates['closing_date'] = clo

        flag = row['is_excluded_business']
        if flag is not None:
            updates['is_not_excluded_business'] = not bool(flag)

        if updates:
            bind.execute(
                sa.update(LEGACY_COMPANY)
                .where(LEGACY_COMPANY.c.id == row['id'])
                .values(**updates)
            )
