"""Create performance tracking tables

Revision ID: 008
Revises: 007
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # Create scraping_schedules table
    op.create_table('scraping_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kol_id', sa.Integer(), nullable=False),
        sa.Column('interval', sa.String(), nullable=False),
        sa.Column('custom_cron', sa.String(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_scraped_at', sa.DateTime(), nullable=True),
        sa.Column('next_scrape_at', sa.DateTime(), nullable=False),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False),
        sa.Column('max_failures', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['kol_id'], ['kols.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scraping_schedules_kol_id'), 'scraping_schedules', ['kol_id'], unique=False)
    op.create_index(op.f('ix_scraping_schedules_is_active'), 'scraping_schedules', ['is_active'], unique=False)
    op.create_index(op.f('ix_scraping_schedules_next_scrape_at'), 'scraping_schedules', ['next_scrape_at'], unique=False)

    # Create posts table
    op.create_table('posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kol_id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('post_id', sa.String(), nullable=False),
        sa.Column('post_url', sa.String(), nullable=False),
        sa.Column('post_type', sa.String(), nullable=False),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('hashtags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('mentions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('posted_at', sa.DateTime(), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('is_campaign_content', sa.Boolean(), nullable=False),
        sa.Column('campaign_keywords_matched', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('initial_likes', sa.Integer(), nullable=False),
        sa.Column('initial_comments', sa.Integer(), nullable=False),
        sa.Column('initial_shares', sa.Integer(), nullable=False),
        sa.Column('initial_views', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['kol_id'], ['kols.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_posts_kol_id'), 'posts', ['kol_id'], unique=False)
    op.create_index(op.f('ix_posts_campaign_id'), 'posts', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_posts_post_id'), 'posts', ['post_id'], unique=False)
    op.create_index(op.f('ix_posts_posted_at'), 'posts', ['posted_at'], unique=False)
    op.create_index(op.f('ix_posts_is_campaign_content'), 'posts', ['is_campaign_content'], unique=False)

    # Create post_metrics table (will be partitioned)
    op.create_table('post_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('likes', sa.Integer(), nullable=False),
        sa.Column('comments', sa.Integer(), nullable=False),
        sa.Column('shares', sa.Integer(), nullable=False),
        sa.Column('views', sa.Integer(), nullable=True),
        sa.Column('saves', sa.Integer(), nullable=True),
        sa.Column('engagement_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('engagement_count', sa.Integer(), nullable=False),
        sa.Column('collected_at', sa.DateTime(), nullable=False),
        sa.Column('collection_interval', sa.String(), nullable=False),
        sa.Column('likes_growth', sa.Integer(), nullable=False),
        sa.Column('comments_growth', sa.Integer(), nullable=False),
        sa.Column('shares_growth', sa.Integer(), nullable=False),
        sa.Column('views_growth', sa.Integer(), nullable=True),
        sa.Column('is_viral', sa.Boolean(), nullable=False),
        sa.Column('is_underperforming', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_post_metrics_post_id'), 'post_metrics', ['post_id'], unique=False)
    op.create_index(op.f('ix_post_metrics_collected_at'), 'post_metrics', ['collected_at'], unique=False)
    op.create_index(op.f('ix_post_metrics_collection_interval'), 'post_metrics', ['collection_interval'], unique=False)

    # Create kol_metrics table (will be partitioned)
    op.create_table('kol_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kol_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('follower_count', sa.Integer(), nullable=False),
        sa.Column('following_count', sa.Integer(), nullable=False),
        sa.Column('post_count', sa.Integer(), nullable=False),
        sa.Column('video_count', sa.Integer(), nullable=True),
        sa.Column('total_likes', sa.Integer(), nullable=True),
        sa.Column('total_comments', sa.Integer(), nullable=True),
        sa.Column('total_shares', sa.Integer(), nullable=True),
        sa.Column('total_views', sa.Integer(), nullable=True),
        sa.Column('engagement_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('avg_likes_per_post', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('avg_comments_per_post', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('avg_views_per_post', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('follower_growth', sa.Integer(), nullable=False),
        sa.Column('follower_growth_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('engagement_growth_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('platform_specific_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('scraped_at', sa.DateTime(), nullable=False),
        sa.Column('scraping_duration_seconds', sa.Float(), nullable=True),
        sa.Column('scraping_success', sa.Boolean(), nullable=False),
        sa.Column('scraping_error', sa.String(), nullable=True),
        sa.Column('is_estimated', sa.Boolean(), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['kol_id'], ['kols.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kol_metrics_kol_id'), 'kol_metrics', ['kol_id'], unique=False)
    op.create_index(op.f('ix_kol_metrics_platform'), 'kol_metrics', ['platform'], unique=False)
    op.create_index(op.f('ix_kol_metrics_scraped_at'), 'kol_metrics', ['scraped_at'], unique=False)

    # Create rate_limit_trackers table
    op.create_table('rate_limit_trackers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('endpoint', sa.String(), nullable=False),
        sa.Column('requests_limit', sa.Integer(), nullable=False),
        sa.Column('window_duration_seconds', sa.Integer(), nullable=False),
        sa.Column('requests_made', sa.Integer(), nullable=False),
        sa.Column('window_start', sa.DateTime(), nullable=False),
        sa.Column('window_end', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('last_request_at', sa.DateTime(), nullable=True),
        sa.Column('reset_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rate_limit_trackers_platform'), 'rate_limit_trackers', ['platform'], unique=False)
    op.create_index(op.f('ix_rate_limit_trackers_window_start'), 'rate_limit_trackers', ['window_start'], unique=False)
    op.create_index(op.f('ix_rate_limit_trackers_window_end'), 'rate_limit_trackers', ['window_end'], unique=False)

    # Create performance_alerts table
    op.create_table('performance_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kol_id', sa.Integer(), nullable=True),
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('post_id', sa.Integer(), nullable=True),
        sa.Column('alert_type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('context_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('threshold_value', sa.Float(), nullable=True),
        sa.Column('actual_value', sa.Float(), nullable=True),
        sa.Column('previous_value', sa.Float(), nullable=True),
        sa.Column('is_acknowledged', sa.Boolean(), nullable=False),
        sa.Column('acknowledged_by', sa.Integer(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledgment_note', sa.String(), nullable=True),
        sa.Column('auto_resolve_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_note', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['kol_id'], ['kols.id'], ),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_performance_alerts_kol_id'), 'performance_alerts', ['kol_id'], unique=False)
    op.create_index(op.f('ix_performance_alerts_campaign_id'), 'performance_alerts', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_performance_alerts_post_id'), 'performance_alerts', ['post_id'], unique=False)
    op.create_index(op.f('ix_performance_alerts_alert_type'), 'performance_alerts', ['alert_type'], unique=False)
    op.create_index(op.f('ix_performance_alerts_severity'), 'performance_alerts', ['severity'], unique=False)
    op.create_index(op.f('ix_performance_alerts_status'), 'performance_alerts', ['status'], unique=False)
    op.create_index(op.f('ix_performance_alerts_is_acknowledged'), 'performance_alerts', ['is_acknowledged'], unique=False)
    op.create_index(op.f('ix_performance_alerts_created_at'), 'performance_alerts', ['created_at'], unique=False)

    # Add new columns to existing tables
    op.add_column('kols', sa.Column('last_scraped_at', sa.DateTime(), nullable=True))
    op.add_column('kols', sa.Column('last_post_check_at', sa.DateTime(), nullable=True))
    op.add_column('kols', sa.Column('average_engagement_rate', sa.Float(), nullable=True))

    op.add_column('campaigns', sa.Column('hashtags', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('campaigns', sa.Column('keywords', postgresql.JSON(astext_type=sa.Text()), nullable=True))

    # Create composite indexes for better performance
    op.create_index('ix_kol_metrics_kol_platform_scraped', 'kol_metrics', ['kol_id', 'platform', 'scraped_at'])
    op.create_index('ix_post_metrics_post_interval_collected', 'post_metrics', ['post_id', 'collection_interval', 'collected_at'])
    op.create_index('ix_scraping_schedules_active_next_scrape', 'scraping_schedules', ['is_active', 'next_scrape_at'])
    op.create_index('ix_performance_alerts_unacknowledged_created', 'performance_alerts', ['is_acknowledged', 'created_at'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_performance_alerts_unacknowledged_created', table_name='performance_alerts')
    op.drop_index('ix_scraping_schedules_active_next_scrape', table_name='scraping_schedules')
    op.drop_index('ix_post_metrics_post_interval_collected', table_name='post_metrics')
    op.drop_index('ix_kol_metrics_kol_platform_scraped', table_name='kol_metrics')

    # Remove columns from existing tables
    op.drop_column('campaigns', 'keywords')
    op.drop_column('campaigns', 'hashtags')
    op.drop_column('kols', 'average_engagement_rate')
    op.drop_column('kols', 'last_post_check_at')
    op.drop_column('kols', 'last_scraped_at')

    # Drop tables
    op.drop_table('performance_alerts')
    op.drop_table('rate_limit_trackers')
    op.drop_table('kol_metrics')
    op.drop_table('post_metrics')
    op.drop_table('posts')
    op.drop_table('scraping_schedules')