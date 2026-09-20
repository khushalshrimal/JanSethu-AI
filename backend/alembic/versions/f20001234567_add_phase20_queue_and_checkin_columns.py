"""add phase20 queue and checkin columns

Revision ID: f20001234567
Revises: e19001234567
Create Date: 2026-09-20 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f20001234567'
down_revision = 'e19001234567'
branch_labels = None
depends_on = None

def upgrade():
    try:
        op.add_column('appointments', sa.Column('queue_token', sa.String(50), nullable=True))
        op.create_index('ix_appointments_queue_token', 'appointments', ['queue_token'], unique=False)
        op.add_column('appointments', sa.Column('checked_in_at', sa.DateTime(), nullable=True))
        op.add_column('appointments', sa.Column('visit_status', sa.String(30), server_default='NOT_CHECKED_IN', nullable=False))
        op.add_column('appointments', sa.Column('consultation_started_at', sa.DateTime(), nullable=True))
        op.add_column('appointments', sa.Column('consultation_completed_at', sa.DateTime(), nullable=True))
    except Exception:
        pass

def downgrade():
    op.drop_column('appointments', 'consultation_completed_at')
    op.drop_column('appointments', 'consultation_started_at')
    op.drop_column('appointments', 'visit_status')
    op.drop_column('appointments', 'checked_in_at')
    op.drop_index('ix_appointments_queue_token', table_name='appointments')
    op.drop_column('appointments', 'queue_token')
