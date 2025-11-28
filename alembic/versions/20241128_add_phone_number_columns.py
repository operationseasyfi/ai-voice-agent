"""Add missing columns to phone_numbers table

Revision ID: 20241128_add_phone_number_columns
Revises: 20241128_add_missing_call_columns
Create Date: 2024-11-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20241128_add_phone_number_columns'
down_revision: Union[str, Sequence[str], None] = '20241128_add_missing'
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
    
    # Create phone number type enum if it doesn't exist
    if not enum_exists('phonenumbertype', connection):
        op.execute("""
            CREATE TYPE phonenumbertype AS ENUM (
                'ai_inbound', 'transfer_high', 'transfer_mid', 'transfer_low', 'outbound'
            )
        """)
    
    # Add number_type column if it doesn't exist
    if not column_exists('phone_numbers', 'number_type', connection):
        # First add as nullable to avoid issues with existing rows
        op.add_column('phone_numbers', 
            sa.Column('number_type', 
                postgresql.ENUM('ai_inbound', 'transfer_high', 'transfer_mid', 'transfer_low', 'outbound', 
                    name='phonenumbertype', create_type=False),
                nullable=True,
                server_default='ai_inbound'
            )
        )
        # Update any NULL values to default
        op.execute("UPDATE phone_numbers SET number_type = 'ai_inbound' WHERE number_type IS NULL")
        # Make it NOT NULL
        op.alter_column('phone_numbers', 'number_type', nullable=False)
    
    # Add signalwire_sid column if it doesn't exist
    if not column_exists('phone_numbers', 'signalwire_sid', connection):
        op.add_column('phone_numbers',
            sa.Column('signalwire_sid', sa.String(length=255), nullable=True)
        )
    
    # Add is_active column if it doesn't exist
    if not column_exists('phone_numbers', 'is_active', connection):
        op.add_column('phone_numbers',
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true')
        )
    
    # Add last_used_at column if it doesn't exist
    if not column_exists('phone_numbers', 'last_used_at', connection):
        op.add_column('phone_numbers',
            sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True)
        )
    
    # Add total_calls column if it doesn't exist
    if not column_exists('phone_numbers', 'total_calls', connection):
        op.add_column('phone_numbers',
            sa.Column('total_calls', sa.String(), nullable=True, server_default='0')
        )
    
    # Add friendly_name column if it doesn't exist
    if not column_exists('phone_numbers', 'friendly_name', connection):
        op.add_column('phone_numbers',
            sa.Column('friendly_name', sa.String(length=255), nullable=True)
        )
    
    # Add description column if it doesn't exist
    if not column_exists('phone_numbers', 'description', connection):
        op.add_column('phone_numbers',
            sa.Column('description', sa.Text(), nullable=True)
        )
    
    # Add created_at column if it doesn't exist
    if not column_exists('phone_numbers', 'created_at', connection):
        op.add_column('phone_numbers',
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True)
        )
    
    # Add updated_at column if it doesn't exist
    if not column_exists('phone_numbers', 'updated_at', connection):
        op.add_column('phone_numbers',
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True)
        )


def downgrade() -> None:
    # Don't drop columns on downgrade to preserve data
    pass

