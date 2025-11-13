"""Add profile picture column to users

Revision ID: 20251110_2300
Revises: 006
Create Date: 2025-11-10 23:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251110_2300'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add profile_picture column to users table."""
    op.add_column(
        'users',
        sa.Column('profile_picture', sa.String(length=255), nullable=True)
    )


def downgrade() -> None:
    """Remove profile_picture column from users table."""
    op.drop_column('users', 'profile_picture')
