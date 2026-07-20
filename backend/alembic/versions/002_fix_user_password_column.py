"""
Fix user password column name.

Renames 'hashed_password' to 'password_hash' in the users table
to match the User model definition.

Revision ID: 002_fix_user_password_column
Revises: 001_initial_schema
Create Date: 2026-07-16
"""
from typing import Sequence, Union
from alembic import op

revision: str = "002_fix_user_password_column"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('users', 'hashed_password', new_column_name='password_hash')
    print("✓ Renamed users.hashed_password -> users.password_hash")


def downgrade() -> None:
    op.alter_column('users', 'password_hash', new_column_name='hashed_password')
