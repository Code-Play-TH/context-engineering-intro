"""Create message tables

Revision ID: 007
Revises: 006
Create Date: 2024-01-15 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Create message type enum
    message_type_enum = postgresql.ENUM(
        'email', 'sms', 'line', 'discord', 'whatsapp',
        name='messagetype',
        create_type=False
    )
    message_type_enum.create(op.get_bind(), checkfirst=True)

    # Create message status enum
    message_status_enum = postgresql.ENUM(
        'draft', 'queued', 'sending', 'sent', 'delivered', 'read', 'failed', 'bounced',
        name='messagestatus',
        create_type=False
    )
    message_status_enum.create(op.get_bind(), checkfirst=True)

    # Create message priority enum
    message_priority_enum = postgresql.ENUM(
        'low', 'normal', 'high', 'urgent',
        name='messagepriority',
        create_type=False
    )
    message_priority_enum.create(op.get_bind(), checkfirst=True)

    # Create message_templates table
    op.create_table('message_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', message_type_enum, nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_message_templates_id'), 'message_templates', ['id'], unique=False)
    op.create_index(op.f('ix_message_templates_name'), 'message_templates', ['name'], unique=False)
    op.create_index(op.f('ix_message_templates_message_type'), 'message_templates', ['message_type'], unique=False)

    # Create messages table
    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', message_type_enum, nullable=False),
        sa.Column('status', message_status_enum, nullable=True),
        sa.Column('priority', message_priority_enum, nullable=True),
        sa.Column('recipient_email', sa.String(length=255), nullable=True),
        sa.Column('recipient_phone', sa.String(length=50), nullable=True),
        sa.Column('recipient_line_id', sa.String(length=255), nullable=True),
        sa.Column('recipient_discord_id', sa.String(length=255), nullable=True),
        sa.Column('sender_email', sa.String(length=255), nullable=True),
        sa.Column('sender_name', sa.String(length=255), nullable=True),
        sa.Column('kol_id', sa.Integer(), nullable=True),
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('brief_id', sa.Integer(), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('sent_by', sa.Integer(), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('external_status', sa.String(length=100), nullable=True),
        sa.Column('message_data', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['brief_id'], ['briefs.id'], ),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['kol_id'], ['kols.id'], ),
        sa.ForeignKeyConstraint(['sent_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['message_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)
    op.create_index(op.f('ix_messages_message_type'), 'messages', ['message_type'], unique=False)
    op.create_index(op.f('ix_messages_status'), 'messages', ['status'], unique=False)


def downgrade():
    # Drop tables
    op.drop_index(op.f('ix_messages_status'), table_name='messages')
    op.drop_index(op.f('ix_messages_message_type'), table_name='messages')
    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_table('messages')
    
    op.drop_index(op.f('ix_message_templates_message_type'), table_name='message_templates')
    op.drop_index(op.f('ix_message_templates_name'), table_name='message_templates')
    op.drop_index(op.f('ix_message_templates_id'), table_name='message_templates')
    op.drop_table('message_templates')
    
    # Drop enums
    message_priority_enum = postgresql.ENUM(name='messagepriority')
    message_priority_enum.drop(op.get_bind(), checkfirst=True)
    
    message_status_enum = postgresql.ENUM(name='messagestatus')
    message_status_enum.drop(op.get_bind(), checkfirst=True)
    
    message_type_enum = postgresql.ENUM(name='messagetype')
    message_type_enum.drop(op.get_bind(), checkfirst=True)