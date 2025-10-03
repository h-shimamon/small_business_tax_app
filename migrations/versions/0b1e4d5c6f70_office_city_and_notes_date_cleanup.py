"""Placeholder revision to restore Alembic history continuity.

The original 0b1e4d5c6f70 migration script was removed before deployment.
This no-op keeps existing environments in sync so later revisions such as
``a54c3d2e1f98`` can run without manual intervention.
"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "0b1e4d5c6f70"
down_revision = "f123456789ab"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op placeholder."""


def downgrade() -> None:
    """No-op placeholder."""
