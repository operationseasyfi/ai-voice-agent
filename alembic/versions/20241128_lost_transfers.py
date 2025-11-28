"""Add lost transfers tracking columns to call_records

Revision ID: 20241128_lost_xfers
Revises: 20241128_phone_cols
Create Date: 2025-11-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20241128_lost_xfers'
down_revision: Union[str, Sequence[str], None] = '20241128_phone_cols'
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


def upgrade() -> None:
    connection = op.get_bind()
    
    # Add transfer_attempt_time - when transfer was attempted
    if not column_exists('call_records', 'transfer_attempt_time', connection):
        op.add_column('call_records',
            sa.Column('transfer_attempt_time', sa.DateTime(timezone=True), nullable=True)
        )
    
    # Add transfer_wait_duration - how long caller waited for transfer pickup
    if not column_exists('call_records', 'transfer_wait_duration', connection):
        op.add_column('call_records',
            sa.Column('transfer_wait_duration', sa.Float(), nullable=True, server_default='0.0')
        )
    
    # Add transfer_answered - whether the transfer was answered by a closer
    if not column_exists('call_records', 'transfer_answered', connection):
        op.add_column('call_records',
            sa.Column('transfer_answered', sa.Boolean(), nullable=True, server_default='false')
        )
    
    # Add disqualification_reason - why caller was ineligible for transfer
    if not column_exists('call_records', 'disqualification_reason', connection):
        op.add_column('call_records',
            sa.Column('disqualification_reason', sa.String(255), nullable=True)
        )


def downgrade() -> None:
    # Don't drop columns on downgrade to preserve data
    pass

