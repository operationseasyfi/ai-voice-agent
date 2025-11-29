"""Fix missing columns in call_records table

Revision ID: 20241129_fix_schema
Revises: 20241128_lost_xfers
Create Date: 2025-11-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20241129_fix_schema'
down_revision: Union[str, Sequence[str], None] = '20241128_lost_xfers'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str, connection) -> bool:
    """Check if a column exists in a table."""
    result = connection.execute(sa.text(
        """
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = :table_name 
            AND column_name = :column_name
        )
        """
    ), {"table_name": table_name, "column_name": column_name})
    return result.scalar()


def enum_exists(enum_name: str, connection) -> bool:
    """Check if an enum type exists."""
    result = connection.execute(sa.text(
        """
        SELECT EXISTS (
            SELECT 1 
            FROM pg_type 
            WHERE typname = :enum_name
        )
        """
    ), {"enum_name": enum_name})
    return result.scalar()


def upgrade() -> None:
    connection = op.get_bind()
    
    # 1. Ensure ENUM types exist
    if not enum_exists('transfertier', connection):
        op.execute("CREATE TYPE transfertier AS ENUM ('high', 'mid', 'low', 'none')")
        
    if not enum_exists('disconnectionreason', connection):
        op.execute("""
            CREATE TYPE disconnectionreason AS ENUM (
                'transferred', 'caller_hangup', 'agent_hangup', 'dnc_detected',
                'error', 'timeout', 'no_answer', 'unknown'
            )
        """)

    # 2. Fix missing columns in call_records
    
    # transfer_tier
    if not column_exists('call_records', 'transfer_tier', connection):
        op.add_column('call_records',
            sa.Column('transfer_tier', 
                postgresql.ENUM('high', 'mid', 'low', 'none', name='transfertier', create_type=False),
                nullable=True
            )
        )

    # disconnection_reason
    if not column_exists('call_records', 'disconnection_reason', connection):
        op.add_column('call_records',
            sa.Column('disconnection_reason',
                postgresql.ENUM(
                    'transferred', 'caller_hangup', 'agent_hangup', 'dnc_detected',
                    'error', 'timeout', 'no_answer', 'unknown',
                    name='disconnectionreason', create_type=False
                ),
                nullable=True
            )
        )

    # transfer_attempt_time
    if not column_exists('call_records', 'transfer_attempt_time', connection):
        op.add_column('call_records',
            sa.Column('transfer_attempt_time', sa.DateTime(timezone=True), nullable=True)
        )

    # transfer_wait_duration
    if not column_exists('call_records', 'transfer_wait_duration', connection):
        op.add_column('call_records',
            sa.Column('transfer_wait_duration', sa.Float(), nullable=True, server_default='0.0')
        )

    # transfer_answered
    if not column_exists('call_records', 'transfer_answered', connection):
        op.add_column('call_records',
            sa.Column('transfer_answered', sa.Boolean(), nullable=True, server_default='false')
        )

    # disqualification_reason
    if not column_exists('call_records', 'disqualification_reason', connection):
        op.add_column('call_records',
            sa.Column('disqualification_reason', sa.String(255), nullable=True)
        )


def downgrade() -> None:
    pass

