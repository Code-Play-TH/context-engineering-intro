"""create_report_generations_table

Revision ID: 010
Revises: 009
Create Date: 2025-10-14 05:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create report_generations table
    op.create_table(
        'report_generations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('report_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('download_url', sa.String(length=500), nullable=True),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('generated_by', sa.Integer(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['report_templates.id'], ),
        sa.ForeignKeyConstraint(['generated_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_report_generations_campaign_id', 'report_generations', ['campaign_id'])
    op.create_index('ix_report_generations_template_id', 'report_generations', ['template_id'])
    op.create_index('ix_report_generations_report_type', 'report_generations', ['report_type'])
    op.create_index('ix_report_generations_status', 'report_generations', ['status'])
    op.create_index('ix_report_generations_generated_by', 'report_generations', ['generated_by'])
    op.create_index('ix_report_generations_generated_at', 'report_generations', ['generated_at'])
    op.create_index('ix_report_generations_expires_at', 'report_generations', ['expires_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_report_generations_expires_at', table_name='report_generations')
    op.drop_index('ix_report_generations_generated_at', table_name='report_generations')
    op.drop_index('ix_report_generations_generated_by', table_name='report_generations')
    op.drop_index('ix_report_generations_status', table_name='report_generations')
    op.drop_index('ix_report_generations_report_type', table_name='report_generations')
    op.drop_index('ix_report_generations_template_id', table_name='report_generations')
    op.drop_index('ix_report_generations_campaign_id', table_name='report_generations')
    
    # Drop table
    op.drop_table('report_generations')