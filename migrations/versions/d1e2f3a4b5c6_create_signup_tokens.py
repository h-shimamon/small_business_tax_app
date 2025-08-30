"""Create signup_tokens table

Revision ID: d1e2f3a4b5c6
Revises: c1d2e3f4a5b6
Create Date: 2025-08-30 00:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd1e2f3a4b5c6'
down_revision = 'c1d2e3f4a5b6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'signup_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
    )
    op.create_index(op.f('ix_signup_tokens_user_id'), 'signup_tokens', ['user_id'])
    op.create_index(op.f('ux_signup_tokens_token_hash'), 'signup_tokens', ['token_hash'], unique=True)


def downgrade():
    op.drop_index(op.f('ux_signup_tokens_token_hash'), table_name='signup_tokens')
    op.drop_index(op.f('ix_signup_tokens_user_id'), table_name='signup_tokens')
    op.drop_table('signup_tokens')
