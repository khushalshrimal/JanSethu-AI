"""add phase19 notification columns

Revision ID: e19001234567
Revises: ad12e3456789
Create Date: 2026-09-20 20:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e19001234567'
down_revision = 'ad12e3456789'
branch_labels = None
depends_on = None

def upgrade():
    try:
        op.add_column('sms_notifications', sa.Column('event_type', sa.String(50), nullable=True))
        op.add_column('sms_notifications', sa.Column('attempt_count', sa.Integer(), server_default='1', nullable=False))
        op.add_column('sms_notifications', sa.Column('last_attempt_at', sa.DateTime(), nullable=True))
        op.add_column('sms_notifications', sa.Column('delivered_at', sa.DateTime(), nullable=True))
    except Exception:
        pass

    try:
        op.add_column('appointments', sa.Column('reminder_sent_at', sa.DateTime(), nullable=True))
    except Exception:
        pass

def downgrade():
    op.drop_column('appointments', 'reminder_sent_at')
    op.drop_column('sms_notifications', 'delivered_at')
    op.drop_column('sms_notifications', 'last_attempt_at')
    op.drop_column('sms_notifications', 'attempt_count')
    op.drop_column('sms_notifications', 'event_type')
