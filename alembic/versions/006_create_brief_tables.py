"""Create brief tables

Revision ID: 006
Revises: 005
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Create brief_templates table
    op.create_table('brief_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_brief_templates_id'), 'brief_templates', ['id'], unique=False)
    op.create_index(op.f('ix_brief_templates_name'), 'brief_templates', ['name'], unique=False)

    # Create brief status enum
    brief_status_enum = postgresql.ENUM(
        'draft', 'pending_review', 'approved', 'sent', 'acknowledged', 
        'in_progress', 'completed', 'rejected',
        name='briefstatus',
        create_type=False
    )
    brief_status_enum.create(op.get_bind(), checkfirst=True)

    # Create briefs table
    op.create_table('briefs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', brief_status_enum, nullable=True),
        sa.Column('brief_data', sa.JSON(), nullable=True),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('kol_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),
        sa.Column('kol_feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['kol_id'], ['kols.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['brief_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_briefs_id'), 'briefs', ['id'], unique=False)
    op.create_index(op.f('ix_briefs_status'), 'briefs', ['status'], unique=False)


def downgrade():
    # Drop tables
    op.drop_index(op.f('ix_briefs_status'), table_name='briefs')
    op.drop_index(op.f('ix_briefs_id'), table_name='briefs')
    op.drop_table('briefs')
    
    op.drop_index(op.f('ix_brief_templates_name'), table_name='brief_templates')
    op.drop_index(op.f('ix_brief_templates_id'), table_name='brief_templates')
    op.drop_table('brief_templates')
    
    # Drop enum
    brief_status_enum = postgresql.ENUM(name='briefstatus')
    brief_status_enum.drop(op.get_bind(), checkfirst=True)