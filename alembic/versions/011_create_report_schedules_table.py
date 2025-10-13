"""create_report_schedules_table

Revision ID: 011
Revises: 010
Create Date: 2025-10-14 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create report_schedules table
    op.create_table(
        'report_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('frequency', sa.String(), nullable=False),
        sa.Column('recipients', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_generated_at', sa.DateTime(), nullable=True),
        sa.Column('next_generation_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['report_templates.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_report_schedules_campaign_id', 'report_schedules', ['campaign_id'])
    op.create_index('ix_report_schedules_template_id', 'report_schedules', ['template_id'])
    op.create_index('ix_report_schedules_frequency', 'report_schedules', ['frequency'])
    op.create_index('ix_report_schedules_is_active', 'report_schedules', ['is_active'])
    op.create_index('ix_report_schedules_last_generated_at', 'report_schedules', ['last_generated_at'])
    op.create_index('ix_report_schedules_next_generation_at', 'report_schedules', ['next_generation_at'])
    op.create_index('ix_report_schedules_created_by', 'report_schedules', ['created_by'])
    op.create_index('ix_report_schedules_created_at', 'report_schedules', ['created_at'])
    
    # Create composite index for active schedules due for generation
    op.create_index('ix_report_schedules_active_due', 'report_schedules', ['is_active', 'next_generation_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_report_schedules_active_due', table_name='report_schedules')
    op.drop_index('ix_report_schedules_created_at', table_name='report_schedules')
    op.drop_index('ix_report_schedules_created_by', table_name='report_schedules')
    op.drop_index('ix_report_schedules_next_generation_at', table_name='report_schedules')
    op.drop_index('ix_report_schedules_last_generated_at', table_name='report_schedules')
    op.drop_index('ix_report_schedules_is_active', table_name='report_schedules')
    op.drop_index('ix_report_schedules_frequency', table_name='report_schedules')
    op.drop_index('ix_report_schedules_template_id', table_name='report_schedules')
    op.drop_index('ix_report_schedules_campaign_id', table_name='report_schedules')
    
    # Drop table
    op.drop_table('report_schedules')