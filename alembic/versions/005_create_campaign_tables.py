"""create campaign tables

Revision ID: 005
Revises: 004
Create Date: 2025-01-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create client_briefs table
    op.create_table(
        'client_briefs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_name', sa.String(length=255), nullable=False),
        sa.Column('campaign_objective', sa.Text(), nullable=False),
        sa.Column('target_audience', JSON, nullable=True),
        sa.Column('budget', sa.Float(), nullable=True),
        sa.Column('brand_guidelines', sa.Text(), nullable=True),
        sa.Column('content_requirements', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    )
    
    # Create campaigns table
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('total_budget', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('objectives', sa.Text(), nullable=True),
        sa.Column('target_audience', JSON, nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    )
    op.create_index('ix_campaigns_name', 'campaigns', ['name'])
    
    # Create campaign_kpis table
    op.create_table(
        'campaign_kpis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('kpi_type', sa.String(length=100), nullable=False),
        sa.Column('target_value', sa.Float(), nullable=False),
        sa.Column('actual_value', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
    )
    op.create_index('ix_campaign_kpis_campaign_id', 'campaign_kpis', ['campaign_id'])
    
    # Create deliverables table
    op.create_table(
        'deliverables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('deliverable_type', sa.String(length=100), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('deadline', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
    )
    op.create_index('ix_deliverables_campaign_id', 'deliverables', ['campaign_id'])


def downgrade() -> None:
    op.drop_index('ix_deliverables_campaign_id', table_name='deliverables')
    op.drop_table('deliverables')
    op.drop_index('ix_campaign_kpis_campaign_id', table_name='campaign_kpis')
    op.drop_table('campaign_kpis')
    op.drop_index('ix_campaigns_name', table_name='campaigns')
    op.drop_table('campaigns')
    op.drop_table('client_briefs')
