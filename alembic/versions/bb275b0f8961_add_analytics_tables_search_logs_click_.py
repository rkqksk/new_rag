"""Add analytics tables (search_logs, click_logs, conversation_logs, sample_requests)

Revision ID: bb275b0f8961
Revises: 1c891cf8d228
Create Date: 2025-11-09 07:36:08.685692

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb275b0f8961'
down_revision: Union[str, None] = '1c891cf8d228'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create search_logs table
    op.create_table(
        'search_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False, index=True),
        sa.Column('query', sa.Text, nullable=False),
        sa.Column('normalized_query', sa.Text, nullable=True),
        sa.Column('filters', sa.Text, nullable=True),  # JSON
        sa.Column('result_count', sa.Integer, nullable=False),
        sa.Column('result_product_indices', sa.Text, nullable=True),  # JSON array
        sa.Column('intent', sa.String(50), nullable=True, index=True),
        sa.Column('product_type', sa.String(50), nullable=True),
        sa.Column('response_time_ms', sa.Integer, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('searched_at', sa.DateTime, nullable=False, index=True),
    )
    op.create_index('ix_search_logs_id', 'search_logs', ['id'])
    op.create_index('ix_search_logs_user_id', 'search_logs', ['user_id'])

    # Create click_logs table
    op.create_table(
        'click_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False, index=True),
        sa.Column('product_idx', sa.String(100), nullable=False, index=True),
        sa.Column('product_code', sa.String(100), nullable=True),
        sa.Column('product_name', sa.String(255), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('material', sa.String(50), nullable=True),
        sa.Column('capacity_ml', sa.Float, nullable=True),
        sa.Column('position', sa.Integer, nullable=True),  # Position in search results
        sa.Column('source_query', sa.Text, nullable=True),
        sa.Column('clicked_at', sa.DateTime, nullable=False, index=True),
    )
    op.create_index('ix_click_logs_id', 'click_logs', ['id'])
    op.create_index('ix_click_logs_user_id', 'click_logs', ['user_id'])

    # Create conversation_logs table
    op.create_table(
        'conversation_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False, index=True),
        sa.Column('message_id', sa.String(100), nullable=False, unique=True),
        sa.Column('role', sa.String(20), nullable=False),  # user, assistant
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('intent', sa.String(50), nullable=True),
        sa.Column('extracted_entities', sa.Text, nullable=True),  # JSON
        sa.Column('response_time_ms', sa.Integer, nullable=True),
        sa.Column('model_used', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, index=True),
    )
    op.create_index('ix_conversation_logs_id', 'conversation_logs', ['id'])
    op.create_index('ix_conversation_logs_user_id', 'conversation_logs', ['user_id'])

    # Create sample_requests table
    op.create_table(
        'sample_requests',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False, index=True),
        sa.Column('product_idx', sa.String(100), nullable=False),
        sa.Column('product_code', sa.String(100), nullable=True),
        sa.Column('product_name', sa.String(255), nullable=True),
        sa.Column('customer_name', sa.String(100), nullable=False),
        sa.Column('customer_email', sa.String(255), nullable=False),
        sa.Column('customer_phone', sa.String(20), nullable=True),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('quantity', sa.Integer, nullable=True),
        sa.Column('message', sa.Text, nullable=True),
        sa.Column('status', sa.String(20), default='pending', nullable=False, index=True),  # pending, approved, rejected
        sa.Column('requested_at', sa.DateTime, nullable=False, index=True),
    )
    op.create_index('ix_sample_requests_id', 'sample_requests', ['id'])
    op.create_index('ix_sample_requests_user_id', 'sample_requests', ['user_id'])
    op.create_index('ix_sample_requests_product_idx', 'sample_requests', ['product_idx'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_sample_requests_product_idx', 'sample_requests')
    op.drop_index('ix_sample_requests_user_id', 'sample_requests')
    op.drop_index('ix_sample_requests_id', 'sample_requests')
    op.drop_index('ix_sample_requests_requested_at', 'sample_requests')
    op.drop_index('ix_sample_requests_status', 'sample_requests')
    op.drop_index('ix_sample_requests_session_id', 'sample_requests')
    op.drop_table('sample_requests')

    op.drop_index('ix_conversation_logs_user_id', 'conversation_logs')
    op.drop_index('ix_conversation_logs_id', 'conversation_logs')
    op.drop_index('ix_conversation_logs_created_at', 'conversation_logs')
    op.drop_index('ix_conversation_logs_session_id', 'conversation_logs')
    op.drop_table('conversation_logs')

    op.drop_index('ix_click_logs_user_id', 'click_logs')
    op.drop_index('ix_click_logs_id', 'click_logs')
    op.drop_index('ix_click_logs_clicked_at', 'click_logs')
    op.drop_index('ix_click_logs_product_idx', 'click_logs')
    op.drop_index('ix_click_logs_session_id', 'click_logs')
    op.drop_table('click_logs')

    op.drop_index('ix_search_logs_user_id', 'search_logs')
    op.drop_index('ix_search_logs_id', 'search_logs')
    op.drop_index('ix_search_logs_searched_at', 'search_logs')
    op.drop_index('ix_search_logs_intent', 'search_logs')
    op.drop_index('ix_search_logs_session_id', 'search_logs')
    op.drop_table('search_logs')
