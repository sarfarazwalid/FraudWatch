"""
Fix refresh_tokens.expires_at timezone handling.

Changes the expires_at column from TIMESTAMP WITHOUT TIME ZONE
to TIMESTAMP WITH TIME ZONE to match the SQLAlchemy model definition
and ensure consistent timezone-aware datetime handling.

Revision ID: 004_fix_refresh_token_timezone
Revises: 003_fix_user_columns
Create Date: 2026-07-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004_fix_refresh_token_timezone"
down_revision: Union[str, None] = "003_fix_user_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Change expires_at column to TIMESTAMP WITH TIME ZONE.

    Uses AT TIME ZONE 'UTC' to safely convert existing timezone-naive
    timestamps to timezone-aware timestamps assuming they were stored in UTC.
    """
    # Get the current column definition
    conn = op.get_bind()

    # Alter the column type to TIMESTAMP WITH TIME ZONE
    # The USING clause converts existing data by assuming it's in UTC
    op.alter_column(
        'refresh_tokens',
        'expires_at',
        type_=sa.DateTime(timezone=True),
        postgresql_using='expires_at AT TIME ZONE \'UTC\'',
        existing_nullable=False,
    )

    print("✓ Changed refresh_tokens.expires_at to TIMESTAMP WITH TIME ZONE")


def downgrade() -> None:
    """
    Revert expires_at column to TIMESTAMP WITHOUT TIME ZONE.

    Converts timezone-aware timestamps back to naive by removing timezone info.
    """
    # Alter the column back to TIMESTAMP WITHOUT TIME ZONE
    op.alter_column(
        'refresh_tokens',
        'expires_at',
        type_=sa.DateTime(timezone=False),
        postgresql_using='expires_at AT TIME ZONE \'UTC\'',
        existing_nullable=False,
    )

    print("✓ Reverted refresh_tokens.expires_at to TIMESTAMP WITHOUT TIME ZONE")
