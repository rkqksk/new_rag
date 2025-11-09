"""Initial migration - SaaS models

Revision ID: 1c891cf8d228
Revises: 
Create Date: 2025-11-09 05:30:12.105018

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c891cf8d228'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('tier', sa.String(50), default='free', nullable=False),
        sa.Column('max_api_calls', sa.Integer, default=1000, nullable=False),
        sa.Column('max_storage_mb', sa.Integer, default=100, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('ix_tenants_id', 'tenants', ['id'])
    op.create_index('ix_tenants_name', 'tenants', ['name'])
    op.create_index('ix_tenants_email', 'tenants', ['email'])

    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('last_used_at', sa.DateTime, nullable=True),
        sa.Column('usage_count', sa.Integer, default=0, nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('ix_api_keys_id', 'api_keys', ['id'])
    op.create_index('ix_api_keys_tenant_id', 'api_keys', ['tenant_id'])
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'])

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), default='member', nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_verified', sa.Boolean, default=False, nullable=False),
        sa.Column('last_login_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])
    op.create_index('ix_users_email', 'users', ['email'])

    # Create invoices table
    op.create_table(
        'invoices',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('stripe_invoice_id', sa.String(255), nullable=True, unique=True),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('amount', sa.Integer, nullable=False),
        sa.Column('currency', sa.String(3), default='usd', nullable=False),
        sa.Column('status', sa.String(50), default='draft', nullable=False),
        sa.Column('period_start', sa.DateTime, nullable=False),
        sa.Column('period_end', sa.DateTime, nullable=False),
        sa.Column('due_date', sa.DateTime, nullable=True),
        sa.Column('paid_at', sa.DateTime, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('invoice_pdf', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('ix_invoices_id', 'invoices', ['id'])
    op.create_index('ix_invoices_tenant_id', 'invoices', ['tenant_id'])
    op.create_index('ix_invoices_stripe_invoice_id', 'invoices', ['stripe_invoice_id'])

    # Create quota_usage table
    op.create_table(
        'quota_usage',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('api_calls_count', sa.Integer, default=0, nullable=False),
        sa.Column('storage_used_mb', sa.Integer, default=0, nullable=False),
        sa.Column('period_start', sa.DateTime, nullable=False),
        sa.Column('period_end', sa.DateTime, nullable=False),
        sa.Column('last_reset_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('ix_quota_usage_id', 'quota_usage', ['id'])
    op.create_index('ix_quota_usage_tenant_id', 'quota_usage', ['tenant_id'])

    # Create usage_logs table
    op.create_table(
        'usage_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('status_code', sa.Integer, nullable=False),
        sa.Column('response_time_ms', sa.Integer, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    op.create_index('ix_usage_logs_id', 'usage_logs', ['id'])
    op.create_index('ix_usage_logs_tenant_id', 'usage_logs', ['tenant_id'])
    op.create_index('ix_usage_logs_user_id', 'usage_logs', ['user_id'])
    op.create_index('ix_usage_logs_endpoint', 'usage_logs', ['endpoint'])
    op.create_index('ix_usage_logs_created_at', 'usage_logs', ['created_at'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_index('ix_usage_logs_created_at', 'usage_logs')
    op.drop_index('ix_usage_logs_endpoint', 'usage_logs')
    op.drop_index('ix_usage_logs_user_id', 'usage_logs')
    op.drop_index('ix_usage_logs_tenant_id', 'usage_logs')
    op.drop_index('ix_usage_logs_id', 'usage_logs')
    op.drop_table('usage_logs')

    op.drop_index('ix_quota_usage_tenant_id', 'quota_usage')
    op.drop_index('ix_quota_usage_id', 'quota_usage')
    op.drop_table('quota_usage')

    op.drop_index('ix_invoices_stripe_invoice_id', 'invoices')
    op.drop_index('ix_invoices_tenant_id', 'invoices')
    op.drop_index('ix_invoices_id', 'invoices')
    op.drop_table('invoices')

    op.drop_index('ix_users_email', 'users')
    op.drop_index('ix_users_tenant_id', 'users')
    op.drop_index('ix_users_id', 'users')
    op.drop_table('users')

    op.drop_index('ix_api_keys_key_hash', 'api_keys')
    op.drop_index('ix_api_keys_tenant_id', 'api_keys')
    op.drop_index('ix_api_keys_id', 'api_keys')
    op.drop_table('api_keys')

    op.drop_index('ix_tenants_email', 'tenants')
    op.drop_index('ix_tenants_name', 'tenants')
    op.drop_index('ix_tenants_id', 'tenants')
    op.drop_table('tenants')
