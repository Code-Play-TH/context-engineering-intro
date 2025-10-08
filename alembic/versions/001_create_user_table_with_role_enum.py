"""create user table with role enum

Revision ID: 001
Revises: 
Create Date: 2025-10-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create user table with role enum.
    
    This migration creates:
    - Role enum type with 4 values (admin, campaign_manager, account_executive, viewer)
    - User table with all required fields for authentication and authorization
    - Indexes on email for fast lookups
    """
    # Create role enum type (check if exists first)
    role_enum = postgresql.ENUM(
        'admin',
        'campaign_manager', 
        'account_executive',
        'viewer',
        name='role',
        create_type=False  # Don't auto-create, we'll handle it manually
    )
    
    # Check if enum exists, create if not
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'role')"
    ))
    enum_exists = result.scalar()
    
    if not enum_exists:
        role_enum.create(conn, checkfirst=True)
    
    # Create user table
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', role_enum, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create unique index on email
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)


def downgrade() -> None:
    """
    Drop user table and role enum.
    """
    # Drop indexes
    op.drop_index(op.f('ix_user_email'), table_name='user')
    
    # Drop table
    op.drop_table('user')
    
    # Drop enum type
    role_enum = postgresql.ENUM(
        'admin',
        'campaign_manager',
        'account_executive', 
        'viewer',
        name='role'
    )
    role_enum.drop(op.get_bind())
