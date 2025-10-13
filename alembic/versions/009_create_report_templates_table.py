"""create_report_templates_table

Revision ID: 009
Revises: 008
Create Date: 2025-10-14 05:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create report_templates table
    op.create_table(
        'report_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('template_type', sa.String(), nullable=False),
        sa.Column('is_shared', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('structure', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('variables', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_report_templates_name', 'report_templates', ['name'])
    op.create_index('ix_report_templates_template_type', 'report_templates', ['template_type'])
    op.create_index('ix_report_templates_is_shared', 'report_templates', ['is_shared'])
    op.create_index('ix_report_templates_created_by', 'report_templates', ['created_by'])
    op.create_index('ix_report_templates_created_at', 'report_templates', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_report_templates_created_at', table_name='report_templates')
    op.drop_index('ix_report_templates_created_by', table_name='report_templates')
    op.drop_index('ix_report_templates_is_shared', table_name='report_templates')
    op.drop_index('ix_report_templates_template_type', table_name='report_templates')
    op.drop_index('ix_report_templates_name', table_name='report_templates')
    
    # Drop table
    op.drop_table('report_templates')