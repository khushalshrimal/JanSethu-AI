"""add operational status columns

Revision ID: ad12e3456789
Revises: 9c01d2345678
Create Date: 2026-09-20 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ad12e3456789'
down_revision = '9c01d2345678'
branch_labels = None
depends_on = None

def upgrade():
    # Define Enums for PostgreSQL
    facility_status = sa.Enum('ACTIVE', 'TEMPORARILY_UNAVAILABLE', 'INACTIVE', name='facilitystatus')
    department_status = sa.Enum('ACTIVE', 'INACTIVE', name='departmentstatus')
    doctor_status = sa.Enum('ACTIVE', 'ON_LEAVE', 'INACTIVE', name='doctorstatus')
    exception_type = sa.Enum('LEAVE', 'HOLIDAY', 'EMERGENCY_DUTY', 'CUSTOM_HOURS', name='exceptiontype')

    # Add columns with fallback handling
    try:
        op.add_column('facilities', sa.Column('status', sa.String(30), server_default='ACTIVE', nullable=False))
        op.add_column('facilities', sa.Column('last_verified_at', sa.DateTime(), nullable=True))
    except Exception:
        pass

    try:
        op.add_column('departments', sa.Column('status', sa.String(30), server_default='ACTIVE', nullable=False))
    except Exception:
        pass

    try:
        op.add_column('doctors', sa.Column('status', sa.String(30), server_default='ACTIVE', nullable=False))
    except Exception:
        pass

    try:
        op.add_column('doctor_schedule_exceptions', sa.Column('exception_type', sa.String(30), server_default='LEAVE', nullable=False))
    except Exception:
        pass

def downgrade():
    op.drop_column('doctor_schedule_exceptions', 'exception_type')
    op.drop_column('doctors', 'status')
    op.drop_column('departments', 'status')
    op.drop_column('facilities', 'last_verified_at')
    op.drop_column('facilities', 'status')
