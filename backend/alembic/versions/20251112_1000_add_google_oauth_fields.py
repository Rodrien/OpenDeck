"""Add Google OAuth fields to users table

Revision ID: 20251112_1000
Revises: 20251111_1900
Create Date: 2025-11-12 10:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251112_1000'
down_revision = '20251111_1900'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add OAuth fields to users table."""
    # Add OAuth columns
    op.add_column('users', sa.Column('oauth_provider', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('oauth_id', sa.String(length=255), nullable=True))
    
    # Make password_hash nullable (OAuth users won't have passwords)
    op.alter_column('users', 'password_hash', nullable=True)
    
    # Add constraints
    op.create_check_constraint(
        'check_oauth_provider',
        'users',
        "oauth_provider IN ('google', 'local') OR oauth_provider IS NULL"
    )

    # Ensure user has either password_hash (local) OR oauth credentials
    op.create_check_constraint(
        'check_auth_method',
        'users',
        "(password_hash IS NOT NULL) OR (oauth_provider IS NOT NULL AND oauth_id IS NOT NULL)"
    )

    # Create unique constraint on (oauth_provider, oauth_id) for OAuth users
    op.create_index(
        'idx_users_oauth_unique',
        'users',
        ['oauth_provider', 'oauth_id'],
        unique=True,
        postgresql_where=sa.text("oauth_provider IS NOT NULL AND oauth_id IS NOT NULL")
    )


def downgrade() -> None:
    """Remove OAuth fields from users table."""
    # Drop constraints and indexes
    op.drop_index('idx_users_oauth_unique', table_name='users')
    op.drop_constraint('check_auth_method', table_name='users', type_='check')
    op.drop_constraint('check_oauth_provider', table_name='users', type_='check')

    # Make password_hash not nullable again
    op.alter_column('users', 'password_hash', nullable=False)

    # Remove OAuth columns
    op.drop_column('users', 'oauth_id')
    op.drop_column('users', 'oauth_provider')