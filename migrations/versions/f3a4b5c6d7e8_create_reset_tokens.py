"""Database schema migration.

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c7d8
Create Date: 2025-08-30 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f3a4b5c6d7e8'
down_revision = 'e2f3a4b5c7d8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'reset_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
    )
    op.create_index(op.f('ix_reset_tokens_user_id'), 'reset_tokens', ['user_id'])
    op.create_index(op.f('ux_reset_tokens_token_hash'), 'reset_tokens', ['token_hash'], unique=True)


def downgrade():
    op.drop_index(op.f('ux_reset_tokens_token_hash'), table_name='reset_tokens')
    op.drop_index(op.f('ix_reset_tokens_user_id'), table_name='reset_tokens')
    op.drop_table('reset_tokens')
