"""create kol tables

Revision ID: 004
Revises: 003
Create Date: 2025-01-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create kols table
    op.create_table(
        'kols',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('niche', ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('tier', sa.String(length=50), nullable=True),
        sa.Column('tags', ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_kols_name', 'kols', ['name'])
    
    # Create social_handles table
    op.create_table(
        'social_handles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kol_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('handle', sa.String(length=255), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=True),
        sa.Column('follower_count', sa.Integer(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_enriched_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['kol_id'], ['kols.id'], ),
    )
    op.create_index('ix_social_handles_kol_id', 'social_handles', ['kol_id'])
    op.create_index('ix_social_handles_platform', 'social_handles', ['platform'])
    
    # Create import_jobs table
    op.create_table(
        'import_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('total_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processed_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('errors', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    )


def downgrade() -> None:
    op.drop_table('import_jobs')
    op.drop_index('ix_social_handles_platform', table_name='social_handles')
    op.drop_index('ix_social_handles_kol_id', table_name='social_handles')
    op.drop_table('social_handles')
    op.drop_index('ix_kols_name', table_name='kols')
    op.drop_table('kols')
