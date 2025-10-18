"""Add topics system

Revision ID: 002
Revises: 001
Create Date: 2025-10-18 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create topics table
    op.create_table(
        'topics',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_topics_name'), 'topics', ['name'], unique=True)

    # Create deck_topics junction table
    op.create_table(
        'deck_topics',
        sa.Column('deck_id', sa.String(length=36), nullable=False),
        sa.Column('topic_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['deck_id'], ['decks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('deck_id', 'topic_id'),
    )

    # Create card_topics junction table
    op.create_table(
        'card_topics',
        sa.Column('card_id', sa.String(length=36), nullable=False),
        sa.Column('topic_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['card_id'], ['cards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('card_id', 'topic_id'),
    )


def downgrade() -> None:
    # Drop junction tables first (due to foreign key constraints)
    op.drop_table('card_topics')
    op.drop_table('deck_topics')

    # Drop topics table
    op.drop_index(op.f('ix_topics_name'), table_name='topics')
    op.drop_table('topics')
