"""Add deck comments and voting system

Revision ID: 006
Revises: 005
Create Date: 2025-11-04 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create deck_comments table
    op.create_table(
        'deck_comments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('deck_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('parent_comment_id', sa.String(length=36), nullable=True),
        sa.Column('is_edited', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['deck_id'], ['decks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['deck_comments.id'], ondelete='CASCADE'),
        sa.CheckConstraint('length(content) <= 5000', name='check_comment_length'),
    )
    op.create_index('idx_deck_comments_deck', 'deck_comments', ['deck_id'])
    op.create_index('idx_deck_comments_user', 'deck_comments', ['user_id'])
    op.create_index('idx_deck_comments_parent', 'deck_comments', ['parent_comment_id'])
    op.create_index('idx_deck_comments_created', 'deck_comments', ['created_at'])

    # Create comment_votes table
    op.create_table(
        'comment_votes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('comment_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('vote_type', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['comment_id'], ['deck_comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint("vote_type IN ('upvote', 'downvote')", name='check_vote_type'),
        sa.UniqueConstraint('comment_id', 'user_id', name='uq_comment_user_vote'),
    )
    op.create_index('idx_comment_votes_comment', 'comment_votes', ['comment_id'])
    op.create_index('idx_comment_votes_user', 'comment_votes', ['user_id'])


def downgrade() -> None:
    # Drop comment_votes table
    op.drop_index('idx_comment_votes_user', table_name='comment_votes')
    op.drop_index('idx_comment_votes_comment', table_name='comment_votes')
    op.drop_table('comment_votes')

    # Drop deck_comments table
    op.drop_index('idx_deck_comments_created', table_name='deck_comments')
    op.drop_index('idx_deck_comments_parent', table_name='deck_comments')
    op.drop_index('idx_deck_comments_user', table_name='deck_comments')
    op.drop_index('idx_deck_comments_deck', table_name='deck_comments')
    op.drop_table('deck_comments')
