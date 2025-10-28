"""Add indexes for document processing

Revision ID: 003
Revises: 002
Create Date: 2025-10-25 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes for document queries."""
    # Index on status for filtering documents by processing status
    op.create_index(
        'ix_documents_status',
        'documents',
        ['status'],
        unique=False
    )

    # Index on deck_id for finding all documents in a deck
    op.create_index(
        'ix_documents_deck_id',
        'documents',
        ['deck_id'],
        unique=False
    )

    # Composite index on user_id and status for common query pattern
    # (e.g., "get all pending documents for user X")
    op.create_index(
        'ix_documents_user_id_status',
        'documents',
        ['user_id', 'status'],
        unique=False
    )


def downgrade() -> None:
    """Remove document indexes."""
    op.drop_index('ix_documents_user_id_status', table_name='documents')
    op.drop_index('ix_documents_deck_id', table_name='documents')
    op.drop_index('ix_documents_status', table_name='documents')
