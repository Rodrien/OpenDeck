"""Add card reports table

Revision ID: 20251111_1830
Revises: 20251110_2300
Create Date: 2025-11-11 18:30:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251111_1830'
down_revision = '20251110_2300'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create card_reports table for reporting incorrect or misleading flashcards."""
    op.create_table(
        'card_reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('card_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_by', sa.String(length=36), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['card_id'], ['cards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id']),
        sa.CheckConstraint("status IN ('pending', 'reviewed', 'resolved', 'dismissed')", name='check_report_status'),
        sa.CheckConstraint('length(reason) >= 10', name='check_report_reason_min_length'),
        sa.CheckConstraint('length(reason) <= 1000', name='check_report_reason_max_length'),
    )

    # Create indexes for efficient queries
    op.create_index('idx_card_reports_card_id', 'card_reports', ['card_id'])
    op.create_index('idx_card_reports_user_id', 'card_reports', ['user_id'])
    op.create_index('idx_card_reports_status', 'card_reports', ['status'])


def downgrade() -> None:
    """Drop card_reports table."""
    op.drop_index('idx_card_reports_status', table_name='card_reports')
    op.drop_index('idx_card_reports_user_id', table_name='card_reports')
    op.drop_index('idx_card_reports_card_id', table_name='card_reports')
    op.drop_table('card_reports')
