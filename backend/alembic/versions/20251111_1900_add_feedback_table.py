"""Add feedback table

Revision ID: 20251111_1900
Revises: 20251111_1830
Create Date: 2025-11-11 19:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251111_1900'
down_revision = '20251111_1830'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create feedback table for user feedback and suggestions."""
    op.create_table(
        'feedback',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('feedback_type', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='new'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.CheckConstraint("feedback_type IN ('bug', 'feature', 'general', 'other')", name='check_feedback_type'),
        sa.CheckConstraint("status IN ('new', 'reviewed', 'resolved')", name='check_feedback_status'),
        sa.CheckConstraint('length(message) >= 10', name='check_feedback_message_min_length'),
        sa.CheckConstraint('length(message) <= 5000', name='check_feedback_message_max_length'),
    )

    # Create indexes for efficient queries
    op.create_index('idx_feedback_user_id', 'feedback', ['user_id'])
    op.create_index('idx_feedback_type', 'feedback', ['feedback_type'])
    op.create_index('idx_feedback_status', 'feedback', ['status'])
    op.create_index('idx_feedback_created_at', 'feedback', ['created_at'])


def downgrade() -> None:
    """Drop feedback table."""
    op.drop_index('idx_feedback_created_at', table_name='feedback')
    op.drop_index('idx_feedback_status', table_name='feedback')
    op.drop_index('idx_feedback_type', table_name='feedback')
    op.drop_index('idx_feedback_user_id', table_name='feedback')
    op.drop_table('feedback')
