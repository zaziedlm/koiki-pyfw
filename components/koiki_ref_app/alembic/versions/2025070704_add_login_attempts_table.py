"""Add login_attempts table for login security monitoring

Revision ID: 2025070704
Revises: 2025070703
Create Date: 2025-07-07 04:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2025070704'
down_revision: Union[str, None] = '2025070703'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add login_attempts table"""
    op.create_table(
        'login_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('is_successful', sa.Boolean(), nullable=False),
        sa.Column('failure_reason', sa.String(length=100), nullable=True),
        sa.Column('attempted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # インデックスの作成
    op.create_index('ix_login_attempts_id', 'login_attempts', ['id'])
    op.create_index('ix_login_attempts_email', 'login_attempts', ['email'])
    op.create_index('ix_login_attempts_user_id', 'login_attempts', ['user_id'])
    op.create_index('ix_login_attempts_ip_address', 'login_attempts', ['ip_address'])
    op.create_index('ix_login_attempts_is_successful', 'login_attempts', ['is_successful'])
    op.create_index('ix_login_attempts_attempted_at', 'login_attempts', ['attempted_at'])


def downgrade() -> None:
    """Drop login_attempts table"""
    op.drop_index('ix_login_attempts_attempted_at', table_name='login_attempts')
    op.drop_index('ix_login_attempts_is_successful', table_name='login_attempts')
    op.drop_index('ix_login_attempts_ip_address', table_name='login_attempts')
    op.drop_index('ix_login_attempts_user_id', table_name='login_attempts')
    op.drop_index('ix_login_attempts_email', table_name='login_attempts')
    op.drop_index('ix_login_attempts_id', table_name='login_attempts')
    op.drop_table('login_attempts')