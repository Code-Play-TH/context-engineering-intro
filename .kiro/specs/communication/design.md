# Design Document - Multi-Channel Communication

## Overview

The Multi-Channel Communication system enables automated and manual messaging with KOLs across Email, Line, Discord, and social media DMs with delivery tracking, message templates, and communication history.

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend   │─────▶│   FastAPI    │─────▶│ PostgreSQL  │
│  Messaging   │◀─────│   Comm       │◀─────│  Database   │
│  Interface   │      │   Service    │      └─────────────┘
└──────────────┘      └──────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
         ┌──────────────┐      ┌──────────────┐
         │    Celery    │      │    Redis     │
         │  (Bulk Send) │      │  (Queue)     │
         └──────────────┘      └──────────────┘
                │
    ┌───────────┼───────────┬───────────┐
    ▼           ▼           ▼           ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ SMTP   │ │  Line  │ │Discord │ │Social  │
│ Server │ │  API   │ │  API   │ │Media   │
└────────┘ └────────┘ └────────┘ └────────┘
```

## Components and Interfaces

### Backend Services

```python
class CommunicationService:
    async def send_message(kol_id: int, message: MessageCreate) -> Message
    async def send_bulk_messages(kol_ids: List[int], message: MessageCreate) -> BulkSendJob
    async def get_message_history(kol_id: int) -> List[Message]
    async def get_conversation_thread(kol_id: int, campaign_id: int) -> List[Message]

class ChannelService:
    async def send_email(to: str, subject: str, body: str, attachments: List[str]) -> MessageStatus
    async def send_line_message(line_user_id: str, message: str) -> MessageStatus
    async def send_discord_message(discord_user_id: str, message: str) -> MessageStatus
    async def send_instagram_dm(username: str, message: str) -> MessageStatus

class TemplateService:
    async def create_template(template_data: TemplateCreate) -> MessageTemplate
    async def get_template(template_id: int) -> MessageTemplate
    async def render_template(template_id: int, variables: dict) -> str

class DeliveryTrackingService:
    async def track_delivery(message_id: int) -> DeliveryStatus
    async def track_open(message_id: int) -> None
    async def track_click(message_id: int, link: str) -> None
```

## Data Models

### Message Model

```python
class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    kol_id: int = Field(foreign_key="kol.id", index=True)
    campaign_id: Optional[int] = Field(foreign_key="campaign.id")
    channel: str  # email, line, discord, instagram_dm, twitter_dm
    direction: str  # outbound, inbound
    subject: Optional[str]  # For email
    body: str
    template_id: Optional[int] = Field(foreign_key="messagetemplate.id")
    status: str  # sending, sent, delivered, read, failed, bounced
    sent_by: int = Field(foreign_key="user.id")
    sent_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    error_message: Optional[str]
```

### MessageTemplate Model

```python
class MessageTemplate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: str  # brief, follow-up, reminder, thank_you
    channel: str  # email, line, discord, all
    subject: Optional[str]  # For email templates
    body: str
    variables: List[str] = Field(sa_column=Column(ARRAY(String)))
    usage_count: int = Field(default=0)
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### BulkSendJob Model

```python
class BulkSendJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: Optional[int] = Field(foreign_key="campaign.id")
    total_recipients: int
    sent_count: int = Field(default=0)
    failed_count: int = Field(default=0)
    status: str  # pending, processing, completed, failed
    started_by: int = Field(foreign_key="user.id")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime]
```

### CommunicationPreference Model

```python
class CommunicationPreference(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    kol_id: int = Field(foreign_key="kol.id", unique=True)
    primary_channel: str
    secondary_channel: Optional[str]
    email: Optional[str]
    line_user_id: Optional[str]
    discord_user_id: Optional[str]
    preferred_time: Optional[str]  # "09:00-17:00"
    timezone: str = Field(default="UTC")
    do_not_disturb_hours: Optional[str]  # "22:00-08:00"
```

## API Endpoints

```python
# Messaging
POST   /api/v1/messages                              # Send message
POST   /api/v1/messages/bulk                         # Send bulk messages
GET    /api/v1/kols/{id}/messages                    # Get message history
GET    /api/v1/campaigns/{id}/messages               # Get campaign messages
GET    /api/v1/messages/{id}                         # Get message details

# Templates
POST   /api/v1/message-templates                     # Create template
GET    /api/v1/message-templates                     # List templates
GET    /api/v1/message-templates/{id}                # Get template
PUT    /api/v1/message-templates/{id}                # Update template
DELETE /api/v1/message-templates/{id}                # Delete template
POST   /api/v1/message-templates/{id}/render         # Render template with variables

# Communication Preferences
GET    /api/v1/kols/{id}/communication-preferences   # Get preferences
PUT    /api/v1/kols/{id}/communication-preferences   # Update preferences

# Delivery Tracking
GET    /api/v1/messages/{id}/delivery-status         # Get delivery status
POST   /api/v1/messages/{id}/track-open              # Track email open (webhook)
POST   /api/v1/messages/{id}/track-click             # Track link click (webhook)
```

## Channel Implementations

### Email Service (SMTP)

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

async def send_email(to: str, subject: str, body: str, attachments: List[str] = None) -> MessageStatus:
    """Send email via SMTP"""
    msg = MIMEMultipart('alternative')
    msg['From'] = settings.SMTP_USER
    msg['To'] = to
    msg['Subject'] = subject

    # Add tracking pixel for open tracking
    tracking_pixel = f'<img src="{settings.API_URL}/api/v1/messages/{message_id}/track-open" width="1" height="1" />'
    html_body = body + tracking_pixel

    msg.attach(MIMEText(body, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))

    # Add attachments
    if attachments:
        for file_path in attachments:
            with open(file_path, 'rb') as f:
                attachment = MIMEApplication(f.read())
                attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file_path))
                msg.attach(attachment)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        return MessageStatus(status="sent", delivered_at=datetime.now())
    except Exception as e:
        return MessageStatus(status="failed", error_message=str(e))
```

### Line Messaging Service

```python
from linebot import LineBotApi
from linebot.models import TextSendMessage

async def send_line_message(line_user_id: str, message: str) -> MessageStatus:
    """Send message via Line Messaging API"""
    line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)

    try:
        line_bot_api.push_message(
            line_user_id,
            TextSendMessage(text=message)
        )
        return MessageStatus(status="sent", delivered_at=datetime.now())
    except Exception as e:
        return MessageStatus(status="failed", error_message=str(e))
```

### Discord Service

```python
import discord

async def send_discord_message(discord_user_id: str, message: str) -> MessageStatus:
    """Send DM via Discord Bot"""
    client = discord.Client()

    try:
        user = await client.fetch_user(int(discord_user_id))
        await user.send(message)
        return MessageStatus(status="sent", delivered_at=datetime.now())
    except Exception as e:
        return MessageStatus(status="failed", error_message=str(e))
```

## Template Rendering

### Variable Replacement

```python
def render_template(template: MessageTemplate, variables: dict) -> str:
    """Replace template variables with actual values"""
    rendered = template.body

    for var_name, var_value in variables.items():
        placeholder = f"{{{{{var_name}}}}}"
        rendered = rendered.replace(placeholder, str(var_value))

    # Check for unreplaced variables
    import re
    unreplaced = re.findall(r'\{\{(\w+)\}\}', rendered)
    if unreplaced:
        raise ValueError(f"Unreplaced variables: {', '.join(unreplaced)}")

    return rendered
```

### Template Variables

```python
async def get_template_variables(kol_id: int, campaign_id: int) -> dict:
    """Get all available variables for template rendering"""
    kol = await get_kol(kol_id)
    campaign = await get_campaign(campaign_id) if campaign_id else None

    variables = {
        'kol_name': kol.name,
        'kol_email': kol.email,
        'kol_niche': ', '.join(kol.niche),
    }

    if campaign:
        variables.update({
            'campaign_name': campaign.name,
            'campaign_start_date': campaign.start_date.strftime('%Y-%m-%d'),
            'campaign_end_date': campaign.end_date.strftime('%Y-%m-%d'),
            'campaign_budget': f"${campaign.total_budget:,.2f}",
            'deadline': campaign.end_date.strftime('%B %d, %Y'),
        })

    return variables
```

## Bulk Messaging

### Bulk Send Implementation

```python
@celery_app.task
def process_bulk_send(job_id: int):
    """Process bulk message sending"""
    job = get_bulk_send_job(job_id)
    kol_ids = get_job_recipients(job_id)

    for kol_id in kol_ids:
        try:
            # Get KOL preferences
            prefs = get_communication_preferences(kol_id)

            # Render message with KOL-specific variables
            variables = get_template_variables(kol_id, job.campaign_id)
            message_body = render_template(job.template_id, variables)

            # Send via preferred channel
            status = send_message_via_channel(
                kol_id=kol_id,
                channel=prefs.primary_channel,
                message=message_body
            )

            if status.status == "sent":
                job.sent_count += 1
            else:
                job.failed_count += 1

        except Exception as e:
            logger.error(f"Failed to send to KOL {kol_id}: {e}")
            job.failed_count += 1

        # Rate limiting: 100 emails per hour
        if job.channel == "email":
            await asyncio.sleep(36)  # 36 seconds between emails

    job.status = "completed"
    job.completed_at = datetime.now()
    save_bulk_send_job(job)
```

## Rate Limiting

### Channel Rate Limits

```python
RATE_LIMITS = {
    'email': {'limit': 100, 'window': 3600},      # 100 per hour
    'line': {'limit': 500, 'window': 3600},       # 500 per hour
    'discord': {'limit': 50, 'window': 60},       # 50 per minute
    'instagram_dm': {'limit': 20, 'window': 3600} # 20 per hour
}

async def check_rate_limit(channel: str) -> bool:
    """Check if rate limit allows sending"""
    limit_config = RATE_LIMITS[channel]

    # Get count from Redis
    key = f"rate_limit:{channel}:{int(time.time() / limit_config['window'])}"
    count = await redis.get(key) or 0

    if int(count) >= limit_config['limit']:
        return False

    # Increment counter
    await redis.incr(key)
    await redis.expire(key, limit_config['window'])

    return True
```

## Performance Considerations

### Database Indexes

```sql
CREATE INDEX idx_message_kol_sent ON message(kol_id, sent_at DESC);
CREATE INDEX idx_message_campaign ON message(campaign_id);
CREATE INDEX idx_message_status ON message(status);
CREATE INDEX idx_bulk_send_job_status ON bulksendjob(status);
```

### Caching

-   Templates: Cache indefinitely (invalidate on update)
-   Communication preferences: Cache for 1 hour
-   Rate limit counters: Redis with TTL

## Testing Strategy

### Unit Tests

-   Template rendering
-   Variable replacement
-   Rate limit checking
-   Channel selection logic

### Integration Tests

-   Email sending end-to-end
-   Line messaging
-   Discord messaging
-   Bulk send workflow
-   Delivery tracking
