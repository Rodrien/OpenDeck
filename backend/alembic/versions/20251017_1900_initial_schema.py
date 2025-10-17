"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-10-17 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create decks table
    op.create_table(
        'decks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('difficulty', sa.Enum('beginner', 'intermediate', 'advanced', name='difficultylevel'), nullable=False),
        sa.Column('card_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_decks_user_id'), 'decks', ['user_id'], unique=False)
    op.create_index(op.f('ix_decks_category'), 'decks', ['category'], unique=False)
    op.create_index(op.f('ix_decks_difficulty'), 'decks', ['difficulty'], unique=False)

    # Create cards table
    op.create_table(
        'cards',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('deck_id', sa.String(length=36), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=500), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['deck_id'], ['decks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_cards_deck_id'), 'cards', ['deck_id'], unique=False)

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('status', sa.Enum('uploaded', 'processing', 'completed', 'failed', name='documentstatus'), nullable=False),
        sa.Column('deck_id', sa.String(length=36), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deck_id'], ['decks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_documents_user_id'), 'documents', ['user_id'], unique=False)
    op.create_index(op.f('ix_documents_status'), 'documents', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_documents_status'), table_name='documents')
    op.drop_index(op.f('ix_documents_user_id'), table_name='documents')
    op.drop_table('documents')

    op.drop_index(op.f('ix_cards_deck_id'), table_name='cards')
    op.drop_table('cards')

    op.drop_index(op.f('ix_decks_difficulty'), table_name='decks')
    op.drop_index(op.f('ix_decks_category'), table_name='decks')
    op.drop_index(op.f('ix_decks_user_id'), table_name='decks')
    op.drop_table('decks')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    # Drop enums
    sa.Enum(name='documentstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='difficultylevel').drop(op.get_bind(), checkfirst=True)
