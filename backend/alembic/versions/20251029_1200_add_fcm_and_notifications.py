"""Add FCM tokens and notifications tables

Revision ID: 004
Revises: 003
Create Date: 2025-10-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user_fcm_tokens and notifications tables."""

    # Create user_fcm_tokens table
    op.create_table(
        'user_fcm_tokens',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('fcm_token', sa.Text, unique=True, nullable=False),
        sa.Column('device_type', sa.String(20), nullable=False),
        sa.Column('device_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Create indexes for user_fcm_tokens
    op.create_index('idx_user_fcm_tokens_user_id', 'user_fcm_tokens', ['user_id'])
    op.create_index(
        'idx_user_fcm_tokens_active',
        'user_fcm_tokens',
        ['user_id', 'is_active'],
        postgresql_where=sa.text('is_active = true')
    )

    # Add composite unique constraint to prevent duplicate token registrations per user
    op.create_unique_constraint(
        'uq_user_fcm_tokens_user_id_fcm_token',
        'user_fcm_tokens',
        ['user_id', 'fcm_token']
    )

    # Add check constraint for device_type
    op.create_check_constraint(
        'ck_user_fcm_tokens_device_type',
        'user_fcm_tokens',
        "device_type IN ('web', 'ios', 'android')"
    )

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('action_url', sa.String(512), nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('image_url', sa.String(512), nullable=True),
        sa.Column('read', sa.Boolean, default=False, nullable=False),
        sa.Column('sent_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('read_at', sa.DateTime, nullable=True),
        sa.Column('fcm_message_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Create indexes for notifications
    op.create_index('idx_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('idx_notifications_user_read', 'notifications', ['user_id', 'read'])
    op.create_index('idx_notifications_created_at', 'notifications', ['created_at'])

    # Add check constraint for notification type
    op.create_check_constraint(
        'ck_notifications_type',
        'notifications',
        "type IN ('info', 'success', 'warning', 'error')"
    )


def downgrade() -> None:
    """Drop user_fcm_tokens and notifications tables."""

    # Drop notifications table and its indexes
    op.drop_index('idx_notifications_created_at', table_name='notifications')
    op.drop_index('idx_notifications_user_read', table_name='notifications')
    op.drop_index('idx_notifications_user_id', table_name='notifications')
    op.drop_table('notifications')

    # Drop user_fcm_tokens table, its indexes, and constraints
    op.drop_constraint('uq_user_fcm_tokens_user_id_fcm_token', 'user_fcm_tokens', type_='unique')
    op.drop_index('idx_user_fcm_tokens_active', table_name='user_fcm_tokens')
    op.drop_index('idx_user_fcm_tokens_user_id', table_name='user_fcm_tokens')
    op.drop_table('user_fcm_tokens')
