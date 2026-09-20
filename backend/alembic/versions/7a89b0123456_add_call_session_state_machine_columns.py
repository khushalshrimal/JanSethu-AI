"""add_call_session_state_machine_columns

Revision ID: 7a89b0123456
Revises: 1403b1820590
Create Date: 2026-09-20 13:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '7a89b0123456'
down_revision: Union[str, None] = '1403b1820590'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('call_sessions', sa.Column('current_state', sa.String(length=50), server_default='GREETING', nullable=False))
    op.add_column('call_sessions', sa.Column('selected_intent', sa.String(length=50), nullable=True))
    op.add_column('call_sessions', sa.Column('selected_facility_id', sa.Integer(), nullable=True))
    op.add_column('call_sessions', sa.Column('selected_department_id', sa.Integer(), nullable=True))
    op.add_column('call_sessions', sa.Column('selected_doctor_id', sa.Integer(), nullable=True))
    op.add_column('call_sessions', sa.Column('selected_date', sa.String(length=20), nullable=True))
    op.add_column('call_sessions', sa.Column('selected_start_time', sa.String(length=20), nullable=True))
    op.add_column('call_sessions', sa.Column('selected_end_time', sa.String(length=20), nullable=True))
    op.add_column('call_sessions', sa.Column('context_json', sa.Text(), nullable=True))
    op.add_column('call_sessions', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))


def downgrade() -> None:
    op.drop_column('call_sessions', 'updated_at')
    op.drop_column('call_sessions', 'context_json')
    op.drop_column('call_sessions', 'selected_end_time')
    op.drop_column('call_sessions', 'selected_start_time')
    op.drop_column('call_sessions', 'selected_date')
    op.drop_column('call_sessions', 'selected_doctor_id')
    op.drop_column('call_sessions', 'selected_department_id')
    op.drop_column('call_sessions', 'selected_facility_id')
    op.drop_column('call_sessions', 'selected_intent')
    op.drop_column('call_sessions', 'current_state')
