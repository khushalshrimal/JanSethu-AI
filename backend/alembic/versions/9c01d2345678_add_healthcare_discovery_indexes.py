"""Add_Healthcare_Discovery_Indexes

Revision ID: 9c01d2345678
Revises: 8b90c1234567
Create Date: 2026-09-20 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '9c01d2345678'
down_revision: Union[str, None] = '8b90c1234567'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    try:
        op.create_index('ix_facilities_facility_type', 'facilities', ['facility_type'], unique=False)
    except Exception:
        pass
    try:
        op.create_index('ix_facilities_is_active', 'facilities', ['is_active'], unique=False)
    except Exception:
        pass
    try:
        op.create_index('ix_facilities_emergency_available', 'facilities', ['emergency_available'], unique=False)
    except Exception:
        pass
    try:
        op.create_index('ix_departments_facility_id', 'departments', ['facility_id'], unique=False)
    except Exception:
        pass
    try:
        op.create_index('ix_doctors_facility_id', 'doctors', ['facility_id'], unique=False)
    except Exception:
        pass
    try:
        op.create_index('ix_doctors_department_id', 'doctors', ['department_id'], unique=False)
    except Exception:
        pass

def downgrade() -> None:
    try:
        op.drop_index('ix_doctors_department_id', table_name='doctors')
    except Exception:
        pass
    try:
        op.drop_index('ix_doctors_facility_id', table_name='doctors')
    except Exception:
        pass
    try:
        op.drop_index('ix_departments_facility_id', table_name='departments')
    except Exception:
        pass
    try:
        op.drop_index('ix_facilities_emergency_available', table_name='facilities')
    except Exception:
        pass
    try:
        op.drop_index('ix_facilities_is_active', table_name='facilities')
    except Exception:
        pass
    try:
        op.drop_index('ix_facilities_facility_type', table_name='facilities')
    except Exception:
        pass
