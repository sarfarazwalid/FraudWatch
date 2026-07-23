from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "005_fix_user_datetime_columns"
down_revision: Union[str, None] = "004_fix_refresh_token_timezone"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Change last_login and locked_until columns to TIMESTAMP WITH TIME ZONE.

    Uses AT TIME ZONE 'UTC' to safely convert existing timezone-naive
    timestamps to timezone-aware timestamps assuming they were stored in UTC.
    """
    # Alter last_login column
    op.alter_column(
        'users',
        'last_login',
        type_=sa.DateTime(timezone=True),
        postgresql_using='last_login AT TIME ZONE \'UTC\'',
        existing_nullable=True,
    )

    # Alter locked_until column
    op.alter_column(
        'users',
        'locked_until',
        type_=sa.DateTime(timezone=True),
        postgresql_using='locked_until AT TIME ZONE \'UTC\'',
        existing_nullable=True,
    )

    print("✓ Changed users.last_login and users.locked_until to TIMESTAMP WITH TIME ZONE")


def downgrade() -> None:
    """
    Revert last_login and locked_until columns to TIMESTAMP WITHOUT TIME ZONE.

    Converts timezone-aware timestamps back to naive by removing timezone info.
    """
    # Alter last_login column back
    op.alter_column(
        'users',
        'last_login',
        type_=sa.DateTime(timezone=False),
        postgresql_using='last_login AT TIME ZONE \'UTC\'',
        existing_nullable=True,
    )

    # Alter locked_until column back
    op.alter_column(
        'users',
        'locked_until',
        type_=sa.DateTime(timezone=False),
        postgresql_using='locked_until AT TIME ZONE \'UTC\'',
        existing_nullable=True,
    )

    print("✓ Reverted users.last_login and users.locked_until to TIMESTAMP WITHOUT TIME ZONE")
