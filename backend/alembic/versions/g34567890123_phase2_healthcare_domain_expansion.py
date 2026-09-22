"""phase2 healthcare domain expansion

Revision ID: g34567890123
Revises: f20001234567
Create Date: 2026-09-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'g34567890123'
down_revision = 'f20001234567'
branch_labels = None
depends_on = None

def upgrade():
    try:
        # Additive columns for facilities
        op.add_column('facilities', sa.Column('area', sa.String(100), nullable=True))
        op.create_index('ix_facilities_area', 'facilities', ['area'], unique=False)
        op.add_column('facilities', sa.Column('city', sa.String(100), nullable=True))
        op.create_index('ix_facilities_city', 'facilities', ['city'], unique=False)
        op.add_column('facilities', sa.Column('email', sa.String(100), nullable=True))
        op.add_column('facilities', sa.Column('is_24x7', sa.Boolean(), server_default='1', nullable=False))
        op.add_column('facilities', sa.Column('ambulance_available', sa.Boolean(), server_default='0', nullable=False))
        op.add_column('facilities', sa.Column('telemedicine_available', sa.Boolean(), server_default='0', nullable=False))
        op.add_column('facilities', sa.Column('emergency_level', sa.String(50), server_default='BASIC_EMERGENCY', nullable=True))
        op.add_column('facilities', sa.Column('icu_available', sa.Boolean(), server_default='0', nullable=False))
        op.add_column('facilities', sa.Column('trauma_support', sa.Boolean(), server_default='0', nullable=False))
        op.add_column('facilities', sa.Column('cardiac_support', sa.Boolean(), server_default='0', nullable=False))
        op.add_column('facilities', sa.Column('pediatric_emergency', sa.Boolean(), server_default='0', nullable=False))
        op.add_column('facilities', sa.Column('is_demo_data', sa.Boolean(), server_default='1', nullable=False))
    except Exception:
        pass

    try:
        # Additive columns for doctors
        op.add_column('doctors', sa.Column('experience_years', sa.Integer(), server_default='5', nullable=False))
        op.add_column('doctors', sa.Column('languages', sa.String(100), server_default='Hindi, English', nullable=False))
        op.add_column('doctors', sa.Column('gender', sa.String(20), server_default='Male', nullable=False))
        op.add_column('doctors', sa.Column('is_demo_data', sa.Boolean(), server_default='1', nullable=False))
    except Exception:
        pass

    try:
        # Create facility_services table
        op.create_table(
            'facility_services',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('facility_id', sa.Integer(), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False),
            sa.Column('department_id', sa.Integer(), sa.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True),
            sa.Column('specialty_name', sa.String(100), nullable=False),
            sa.Column('is_available', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('emergency_supported', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('outpatient_supported', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('inpatient_supported', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False)
        )
        op.create_index('ix_facility_services_facility_id', 'facility_services', ['facility_id'], unique=False)
        op.create_index('ix_facility_services_specialty_name', 'facility_services', ['specialty_name'], unique=False)
    except Exception:
        pass

    try:
        # Create appointment_slots table
        op.create_table(
            'appointment_slots',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('doctor_id', sa.Integer(), sa.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False),
            sa.Column('facility_id', sa.Integer(), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False),
            sa.Column('department_id', sa.Integer(), sa.ForeignKey('departments.id', ondelete='CASCADE'), nullable=False),
            sa.Column('slot_date', sa.Date(), nullable=False),
            sa.Column('start_time', sa.Time(), nullable=False),
            sa.Column('end_time', sa.Time(), nullable=False),
            sa.Column('status', sa.String(20), server_default='AVAILABLE', nullable=False),
            sa.Column('is_demo_data', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.UniqueConstraint('doctor_id', 'slot_date', 'start_time', name='uq_doctor_slot_date_start')
        )
        op.create_index('ix_appointment_slots_doctor_id', 'appointment_slots', ['doctor_id'], unique=False)
        op.create_index('ix_appointment_slots_facility_id', 'appointment_slots', ['facility_id'], unique=False)
        op.create_index('ix_appointment_slots_slot_date', 'appointment_slots', ['slot_date'], unique=False)
        op.create_index('ix_appointment_slots_status', 'appointment_slots', ['status'], unique=False)
    except Exception:
        pass

    try:
        # Create ambulances table
        op.create_table(
            'ambulances',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('facility_id', sa.Integer(), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False),
            sa.Column('vehicle_identifier', sa.String(50), nullable=False),
            sa.Column('ambulance_type', sa.String(30), server_default='BASIC_LIFE_SUPPORT', nullable=False),
            sa.Column('status', sa.String(20), server_default='AVAILABLE', nullable=False),
            sa.Column('latitude', sa.Float(), nullable=True),
            sa.Column('longitude', sa.Float(), nullable=True),
            sa.Column('driver_name', sa.String(100), nullable=True),
            sa.Column('driver_phone', sa.String(20), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('is_demo_data', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False)
        )
        op.create_index('ix_ambulances_facility_id', 'ambulances', ['facility_id'], unique=False)
        op.create_index('ix_ambulances_vehicle_identifier', 'ambulances', ['vehicle_identifier'], unique=True)
        op.create_index('ix_ambulances_status', 'ambulances', ['status'], unique=False)
    except Exception:
        pass

def downgrade():
    op.drop_table('ambulances')
    op.drop_table('appointment_slots')
    op.drop_table('facility_services')
    op.drop_column('doctors', 'is_demo_data')
    op.drop_column('doctors', 'gender')
    op.drop_column('doctors', 'languages')
    op.drop_column('doctors', 'experience_years')
    op.drop_column('facilities', 'is_demo_data')
    op.drop_column('facilities', 'pediatric_emergency')
    op.drop_column('facilities', 'cardiac_support')
    op.drop_column('facilities', 'trauma_support')
    op.drop_column('facilities', 'icu_available')
    op.drop_column('facilities', 'emergency_level')
    op.drop_column('facilities', 'telemedicine_available')
    op.drop_column('facilities', 'ambulance_available')
    op.drop_column('facilities', 'is_24x7')
    op.drop_column('facilities', 'email')
    op.drop_column('facilities', 'city')
    op.drop_column('facilities', 'area')
