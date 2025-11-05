"""Add spaced repetition and study sessions

Revision ID: 005
Revises: 004
Create Date: 2025-11-04 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create card_reviews table
    op.create_table(
        'card_reviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('card_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('review_date', sa.DateTime(), nullable=False),
        sa.Column('quality', sa.Integer(), nullable=False),
        sa.Column('ease_factor', sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column('interval_days', sa.Integer(), nullable=False),
        sa.Column('repetitions', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['card_id'], ['cards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint('quality >= 0 AND quality <= 5', name='check_quality_range'),
    )
    op.create_index('idx_card_reviews_card_user', 'card_reviews', ['card_id', 'user_id'])
    op.create_index('idx_card_reviews_user_date', 'card_reviews', ['user_id', 'review_date'])

    # Create study_sessions table
    op.create_table(
        'study_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('deck_id', sa.String(length=36), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('cards_reviewed', sa.Integer(), nullable=False, default=0),
        sa.Column('cards_correct', sa.Integer(), nullable=False, default=0),
        sa.Column('cards_incorrect', sa.Integer(), nullable=False, default=0),
        sa.Column('total_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('session_type', sa.String(length=50), nullable=False, default='review'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deck_id'], ['decks.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_study_sessions_user', 'study_sessions', ['user_id'])
    op.create_index('idx_study_sessions_deck', 'study_sessions', ['deck_id'])
    op.create_index('idx_study_sessions_started', 'study_sessions', ['started_at'])

    # Extend cards table with spaced repetition fields
    op.add_column('cards', sa.Column('ease_factor', sa.Numeric(precision=4, scale=2), nullable=False, server_default='2.5'))
    op.add_column('cards', sa.Column('interval_days', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('cards', sa.Column('repetitions', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('cards', sa.Column('next_review_date', sa.DateTime(), nullable=True))
    op.add_column('cards', sa.Column('is_learning', sa.Boolean(), nullable=False, server_default='true'))

    # Create index for efficient due card queries
    op.create_index('idx_cards_next_review', 'cards', ['deck_id', 'next_review_date'])


def downgrade() -> None:
    # Drop indexes on cards table
    op.drop_index('idx_cards_next_review', table_name='cards')

    # Remove spaced repetition columns from cards table
    op.drop_column('cards', 'is_learning')
    op.drop_column('cards', 'next_review_date')
    op.drop_column('cards', 'repetitions')
    op.drop_column('cards', 'interval_days')
    op.drop_column('cards', 'ease_factor')

    # Drop study_sessions table
    op.drop_index('idx_study_sessions_started', table_name='study_sessions')
    op.drop_index('idx_study_sessions_deck', table_name='study_sessions')
    op.drop_index('idx_study_sessions_user', table_name='study_sessions')
    op.drop_table('study_sessions')

    # Drop card_reviews table
    op.drop_index('idx_card_reviews_user_date', table_name='card_reviews')
    op.drop_index('idx_card_reviews_card_user', table_name='card_reviews')
    op.drop_table('card_reviews')
