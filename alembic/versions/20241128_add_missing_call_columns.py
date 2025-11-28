"""Add missing transfer_tier and disconnection_reason columns to call_records

Revision ID: 20241128_add_missing
Revises: 20241125_multi_tenant
Create Date: 2025-11-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20241128_add_missing'
down_revision = '20241125_multi_tenant'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    transfer_tier_enum = postgresql.ENUM('high', 'mid', 'low', 'none', name='transfertier', create_type=False)
    disconnection_reason_enum = postgresql.ENUM(
        'transferred', 'caller_hangup', 'agent_hangup', 'dnc_detected', 
        'error', 'timeout', 'no_answer', 'unknown',
        name='disconnectionreason', create_type=False
    )
    
    # Create the enum types in the database
    transfer_tier_enum.create(op.get_bind(), checkfirst=True)
    disconnection_reason_enum.create(op.get_bind(), checkfirst=True)
    
    # Add columns to call_records if they don't exist
    # Using raw SQL for better control
    conn = op.get_bind()
    
    # Check and add transfer_tier column
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'call_records' AND column_name = 'transfer_tier'"
    ))
    if not result.fetchone():
        op.add_column('call_records', 
            sa.Column('transfer_tier', postgresql.ENUM('high', 'mid', 'low', 'none', name='transfertier', create_type=False), nullable=True)
        )
    
    # Check and add disconnection_reason column
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'call_records' AND column_name = 'disconnection_reason'"
    ))
    if not result.fetchone():
        op.add_column('call_records',
            sa.Column('disconnection_reason', postgresql.ENUM(
                'transferred', 'caller_hangup', 'agent_hangup', 'dnc_detected',
                'error', 'timeout', 'no_answer', 'unknown',
                name='disconnectionreason', create_type=False
            ), nullable=True)
        )


def downgrade() -> None:
    # Remove columns
    op.drop_column('call_records', 'transfer_tier')
    op.drop_column('call_records', 'disconnection_reason')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS transfertier")
    op.execute("DROP TYPE IF EXISTS disconnectionreason")

