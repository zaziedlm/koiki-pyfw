"""Add password_reset_tokens table for password reset functionality

Revision ID: 2025070703
Revises: 2025070702
Create Date: 2025-07-07 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2025070703'
down_revision: Union[str, None] = '2025070702'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add password_reset_tokens table"""
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    
    # インデックスの作成
    op.create_index('ix_password_reset_tokens_id', 'password_reset_tokens', ['id'])
    op.create_index('ix_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'])
    op.create_index('ix_password_reset_tokens_token_hash', 'password_reset_tokens', ['token_hash'])
    op.create_index('ix_password_reset_tokens_expires_at', 'password_reset_tokens', ['expires_at'])
    op.create_index('ix_password_reset_tokens_is_used', 'password_reset_tokens', ['is_used'])


def downgrade() -> None:
    """Drop password_reset_tokens table"""
    op.drop_index('ix_password_reset_tokens_is_used', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_expires_at', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_token_hash', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_user_id', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_id', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')