"""
Fix user table columns.

Adds missing columns to the users table to match the User model:
- is_verified (replaces email_verified + phone_verified)
- timezone
- language
- profile_image_url
- role_id (foreign key to roles)

Revision ID: 003_fix_user_columns
Revises: 002_fix_user_password_column
Create Date: 2026-07-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

revision: str = "003_fix_user_columns"
down_revision: Union[str, None] = "002_fix_user_password_column"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns
    op.add_column('users', sa.Column('is_verified', sa.Boolean, nullable=False, server_default='false'))
    op.add_column('users', sa.Column('timezone', sa.String(50), nullable=True, server_default='UTC'))
    op.add_column('users', sa.Column('language', sa.String(10), nullable=True, server_default='en'))
    op.add_column('users', sa.Column('profile_image_url', sa.Text, nullable=True))
    op.add_column('users', sa.Column('role_id', PG_UUID(as_uuid=True), nullable=True))

    # Add foreign key for role_id
    op.create_foreign_key('fk_users_role_id', 'users', 'roles', ['role_id'], ['id'], ondelete='SET NULL')

    # Drop old columns that don't exist in the model
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'phone_verified')

    print("✓ Added missing user columns and removed obsolete ones")


def downgrade() -> None:
    # Re-add old columns
    op.add_column('users', sa.Column('email_verified', sa.Boolean, nullable=False, server_default='false'))
    op.add_column('users', sa.Column('phone_verified', sa.Boolean, nullable=False, server_default='false'))

    # Drop new columns
    op.drop_constraint('fk_users_role_id', 'users', type_='foreignkey')
    op.drop_column('users', 'role_id')
    op.drop_column('users', 'profile_image_url')
    op.drop_column('users', 'language')
    op.drop_column('users', 'timezone')
    op.drop_column('users', 'is_verified')
