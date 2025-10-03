"""Database schema migration: create reset_tokens table and indices.

Revision ID: f3a4b5c6d7e8
Revises: 
Create Date: 2025-08-11 23:20:57.381104
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3a4b5c6d7e8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('reset_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('token_hash', sa.String(length=255), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reset_tokens_user_id'), 'reset_tokens', ['user_id'], unique=False)
    op.create_index(op.f('ux_reset_tokens_token_hash'), 'reset_tokens', ['token_hash'], unique=True)


def downgrade():
    op.drop_index(op.f('ux_reset_tokens_token_hash'), table_name='reset_tokens')
    op.drop_index(op.f('ix_reset_tokens_user_id'), table_name='reset_tokens')
    op.drop_table('reset_tokens')
