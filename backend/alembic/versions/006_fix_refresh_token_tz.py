from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "006_fix_refresh_token_tz"
down_revision: Union[str, None] = "005_fix_user_datetime_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix refresh_tokens.expires_at
    op.alter_column(
        'refresh_tokens',
        'expires_at',
        type_=sa.DateTime(timezone=True),
        postgresql_using='expires_at AT TIME ZONE \'UTC\'',
        existing_nullable=False,
        existing_type=sa.DateTime(),
    )
    print("✓ Ensured refresh_tokens.expires_at is TIMESTAMP WITH TIME ZONE")

    # Fix user_sessions.expires_at
    op.alter_column(
        'user_sessions',
        'expires_at',
        type_=sa.DateTime(timezone=True),
        postgresql_using='expires_at AT TIME ZONE \'UTC\'',
        existing_nullable=False,
        existing_type=sa.DateTime(),
    )
    print("✓ Ensured user_sessions.expires_at is TIMESTAMP WITH TIME ZONE")

    # Fix user_sessions.last_activity
    op.alter_column(
        'user_sessions',
        'last_activity',
        type_=sa.DateTime(timezone=True),
        postgresql_using='last_activity AT TIME ZONE \'UTC\'',
        existing_nullable=False,
        existing_type=sa.DateTime(),
    )
    print("✓ Ensured user_sessions.last_activity is TIMESTAMP WITH TIME ZONE")


def downgrade() -> None:
    """
    Revert datetime columns to TIMESTAMP WITHOUT TIME ZONE.
    """
    # Revert refresh_tokens.expires_at
    op.alter_column(
        'refresh_tokens',
        'expires_at',
        type_=sa.DateTime(timezone=False),
        postgresql_using='expires_at AT TIME ZONE \'UTC\'',
        existing_nullable=False,
        existing_type=sa.DateTime(timezone=True),
    )
    print("✓ Reverted refresh_tokens.expires_at to TIMESTAMP WITHOUT TIME ZONE")

    # Revert user_sessions.expires_at
    op.alter_column(
        'user_sessions',
        'expires_at',
        type_=sa.DateTime(timezone=False),
        postgresql_using='expires_at AT TIME ZONE \'UTC\'',
        existing_nullable=False,
        existing_type=sa.DateTime(timezone=True),
    )
    print("✓ Reverted user_sessions.expires_at to TIMESTAMP WITHOUT TIME ZONE")

    # Revert user_sessions.last_activity
    op.alter_column(
        'user_sessions',
        'last_activity',
        type_=sa.DateTime(timezone=False),
        postgresql_using='last_activity AT TIME ZONE \'UTC\'',
        existing_nullable=False,
        existing_type=sa.DateTime(timezone=True),
    )
    print("✓ Reverted user_sessions.last_activity to TIMESTAMP WITHOUT TIME ZONE")
