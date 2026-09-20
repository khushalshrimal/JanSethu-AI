"""add_telephony_provider_columns

Revision ID: 8b90c1234567
Revises: 7a89b0123456
Create Date: 2026-09-20 14:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '8b90c1234567'
down_revision: Union[str, None] = '7a89b0123456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('call_sessions', sa.Column('provider', sa.String(length=50), server_default='development', nullable=False))
    op.add_column('call_sessions', sa.Column('provider_call_id', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_call_sessions_provider_call_id'), 'call_sessions', ['provider_call_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_call_sessions_provider_call_id'), table_name='call_sessions')
    op.drop_column('call_sessions', 'provider_call_id')
    op.drop_column('call_sessions', 'provider')
