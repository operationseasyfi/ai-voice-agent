"""Multi-tenant schema with clients, agents, phone_numbers, call_records, and dnc_list

Revision ID: 20241125_multi_tenant
Revises: 98f5f2f24fcc
Create Date: 2024-11-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20241125_multi_tenant'
down_revision: Union[str, Sequence[str], None] = '98f5f2f24fcc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE disconnectionreason AS ENUM ('transferred', 'caller_hangup', 'agent_hangup', 'dnc_detected', 'error', 'timeout', 'no_answer', 'unknown')")
    op.execute("CREATE TYPE transfertier AS ENUM ('high', 'mid', 'low', 'none')")
    op.execute("CREATE TYPE phonenumbertype AS ENUM ('ai_inbound', 'transfer_high', 'transfer_mid', 'transfer_low', 'outbound')")
    
    # Create clients table
    op.create_table('clients',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('billing_email', sa.String(length=255), nullable=True),
        sa.Column('contact_name', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('transfer_config', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clients_slug'), 'clients', ['slug'], unique=True)
    
    # Add client_id to users table
    op.add_column('users', sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_users_client_id', 'users', 'clients', ['client_id'], ['id'])
    op.create_index(op.f('ix_users_client_id'), 'users', ['client_id'], unique=False)
    
    # Create agents table
    op.create_table('agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('voice_config', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('prompt_config', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('routing_config', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{"high_threshold": 35000, "mid_threshold": 10000}'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('stats_cache', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agents_client_id'), 'agents', ['client_id'], unique=False)
    
    # Create phone_numbers table
    op.create_table('phone_numbers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('number', sa.String(length=50), nullable=False),
        sa.Column('friendly_name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('number_type', sa.Enum('ai_inbound', 'transfer_high', 'transfer_mid', 'transfer_low', 'outbound', name='phonenumbertype'), nullable=False, server_default='ai_inbound'),
        sa.Column('signalwire_sid', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_calls', sa.String(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_phone_numbers_client_id'), 'phone_numbers', ['client_id'], unique=False)
    op.create_index(op.f('ix_phone_numbers_agent_id'), 'phone_numbers', ['agent_id'], unique=False)
    op.create_index(op.f('ix_phone_numbers_number'), 'phone_numbers', ['number'], unique=False)
    
    # Create call_records table
    op.create_table('call_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('call_sid', sa.String(length=255), nullable=True),
        sa.Column('from_number', sa.String(length=50), nullable=True),
        sa.Column('to_number', sa.String(length=50), nullable=True),
        sa.Column('direction', sa.String(length=20), nullable=True, server_default='inbound'),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('disconnection_reason', sa.Enum('transferred', 'caller_hangup', 'agent_hangup', 'dnc_detected', 'error', 'timeout', 'no_answer', 'unknown', name='disconnectionreason'), nullable=True, server_default='unknown'),
        sa.Column('transfer_tier', sa.Enum('high', 'mid', 'low', 'none', name='transfertier'), nullable=True, server_default='none'),
        sa.Column('transfer_did', sa.String(length=50), nullable=True),
        sa.Column('transfer_success', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('transfer_duration', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('is_dnc_flagged', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('dnc_phrase_detected', sa.Text(), nullable=True),
        sa.Column('concurrent_calls_at_start', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('lead_name', sa.String(length=255), nullable=True),
        sa.Column('loan_amount', sa.Float(), nullable=True),
        sa.Column('funds_purpose', sa.Text(), nullable=True),
        sa.Column('employment_status', sa.String(length=100), nullable=True),
        sa.Column('credit_card_debt', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('personal_loan_debt', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('other_debt', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('total_debt', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('monthly_income', sa.Float(), nullable=True),
        sa.Column('ssn_last_four', sa.String(length=4), nullable=True),
        sa.Column('intake_data', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('recording_url', sa.Text(), nullable=True),
        sa.Column('recording_duration', sa.Float(), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('conversation_summary', sa.Text(), nullable=True),
        sa.Column('steps_completed', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('call_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('call_ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_call_records_call_sid'), 'call_records', ['call_sid'], unique=True)
    op.create_index(op.f('ix_call_records_client_id'), 'call_records', ['client_id'], unique=False)
    op.create_index(op.f('ix_call_records_agent_id'), 'call_records', ['agent_id'], unique=False)
    op.create_index(op.f('ix_call_records_from_number'), 'call_records', ['from_number'], unique=False)
    
    # Create dnc_list table
    op.create_table('dnc_list',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('phone_number', sa.String(length=50), nullable=False),
        sa.Column('call_record_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('detection_method', sa.String(length=50), nullable=True, server_default='auto'),
        sa.Column('detected_phrase', sa.Text(), nullable=True),
        sa.Column('added_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('flagged_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['call_record_id'], ['call_records.id'], ),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.ForeignKeyConstraint(['added_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dnc_list_client_id'), 'dnc_list', ['client_id'], unique=False)
    op.create_index(op.f('ix_dnc_list_phone_number'), 'dnc_list', ['phone_number'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_index(op.f('ix_dnc_list_phone_number'), table_name='dnc_list')
    op.drop_index(op.f('ix_dnc_list_client_id'), table_name='dnc_list')
    op.drop_table('dnc_list')
    
    op.drop_index(op.f('ix_call_records_from_number'), table_name='call_records')
    op.drop_index(op.f('ix_call_records_agent_id'), table_name='call_records')
    op.drop_index(op.f('ix_call_records_client_id'), table_name='call_records')
    op.drop_index(op.f('ix_call_records_call_sid'), table_name='call_records')
    op.drop_table('call_records')
    
    op.drop_index(op.f('ix_phone_numbers_number'), table_name='phone_numbers')
    op.drop_index(op.f('ix_phone_numbers_agent_id'), table_name='phone_numbers')
    op.drop_index(op.f('ix_phone_numbers_client_id'), table_name='phone_numbers')
    op.drop_table('phone_numbers')
    
    op.drop_index(op.f('ix_agents_client_id'), table_name='agents')
    op.drop_table('agents')
    
    # Remove client_id from users
    op.drop_index(op.f('ix_users_client_id'), table_name='users')
    op.drop_constraint('fk_users_client_id', 'users', type_='foreignkey')
    op.drop_column('users', 'client_id')
    
    op.drop_index(op.f('ix_clients_slug'), table_name='clients')
    op.drop_table('clients')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS phonenumbertype")
    op.execute("DROP TYPE IF EXISTS transfertier")
    op.execute("DROP TYPE IF EXISTS disconnectionreason")

