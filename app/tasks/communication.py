"""
Communication background tasks for KOL Management System.
Handles bulk messaging, email campaigns, and scheduled communications.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from celery import current_task
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app, priority_task
from app.core.database import get_db
from app.services.communication import (
    communication_factory, send_email, send_discord_message, send_line_message,
    MessageResult, MessagePriority
)
from app.models.communication import Message, MessageTemplate, FollowUpSchedule, MessageStatus, ScheduleStatus
from app.models.kol import KOL
from app.models.campaign import Campaign
from app.schemas.communication import MessageCreate

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def send_bulk_emails(self, message_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Send bulk emails to multiple recipients.

    Args:
        message_configs: List of email configurations

    Returns:
        Dict with send results and statistics
    """
    task_id = self.request.id
    logger.info(f"Starting bulk email task {task_id} with {len(message_configs)} messages")

    results = {
        "task_id": task_id,
        "total_messages": len(message_configs),
        "successful": 0,
        "failed": 0,
        "results": []
    }

    try:
        # Update task progress
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": len(message_configs), "status": "Starting bulk send"}
        )

        # Process messages in batches of 10 for better performance
        batch_size = 10
        for i in range(0, len(message_configs), batch_size):
            batch = message_configs[i:i + batch_size]

            # Send batch concurrently
            import asyncio

            async def send_batch():
                batch_results = []
                for j, config in enumerate(batch):
                    try:
                        result = await send_email(
                            recipient=config["recipient"],
                            subject=config["subject"],
                            content=config["content"],
                            sender=config.get("sender"),
                            html=config.get("html", False),
                            attachments=config.get("attachments"),
                            provider=config.get("provider", "sendgrid")
                        )

                        batch_results.append({
                            "recipient": config["recipient"],
                            "success": result.success,
                            "message_id": result.message_id,
                            "error": result.error
                        })

                        if result.success:
                            results["successful"] += 1
                        else:
                            results["failed"] += 1

                        # Update progress
                        current_progress = i + j + 1
                        current_task.update_state(
                            state="PROGRESS",
                            meta={
                                "current": current_progress,
                                "total": len(message_configs),
                                "status": f"Sent {current_progress}/{len(message_configs)}"
                            }
                        )

                    except Exception as e:
                        logger.error(f"Failed to send email to {config['recipient']}: {str(e)}")
                        batch_results.append({
                            "recipient": config["recipient"],
                            "success": False,
                            "error": str(e)
                        })
                        results["failed"] += 1

                return batch_results

            # Run batch
            batch_results = asyncio.run(send_batch())
            results["results"].extend(batch_results)

            # Small delay between batches to respect rate limits
            import time
            time.sleep(1)

        logger.info(f"Bulk email task {task_id} completed: {results['successful']} sent, {results['failed']} failed")
        return results

    except Exception as e:
        logger.error(f"Bulk email task {task_id} failed: {str(e)}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(bind=True)
def send_campaign_messages(self, campaign_id: int, message_template_id: int, kol_ids: List[int]) -> Dict[str, Any]:
    """
    Send campaign messages to multiple KOLs using a template.

    Args:
        campaign_id: Campaign ID
        message_template_id: Message template ID
        kol_ids: List of KOL IDs

    Returns:
        Dict with send results
    """
    task_id = self.request.id
    logger.info(f"Starting campaign messaging task {task_id} for campaign {campaign_id}")

    # Get database session
    with next(get_db()) as db:
        try:
            # Get campaign and template
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
            template = db.query(MessageTemplate).filter(MessageTemplate.id == message_template_id).first()

            if not campaign or not template:
                raise ValueError("Campaign or template not found")

            # Get KOLs
            kols = db.query(KOL).filter(KOL.id.in_(kol_ids)).all()

            results = {
                "task_id": task_id,
                "campaign_id": campaign_id,
                "template_id": message_template_id,
                "total_kols": len(kols),
                "successful": 0,
                "failed": 0,
                "messages": []
            }

            # Update progress
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 0, "total": len(kols), "status": "Preparing messages"}
            )

            # Send messages to each KOL
            for i, kol in enumerate(kols):
                try:
                    # Prepare template variables
                    template_vars = {
                        "kol_name": kol.name,
                        "campaign_title": campaign.title,
                        "campaign_description": campaign.description,
                        "start_date": campaign.start_date.strftime("%Y-%m-%d") if campaign.start_date else "",
                        "end_date": campaign.end_date.strftime("%Y-%m-%d") if campaign.end_date else "",
                    }

                    # Render content
                    service = communication_factory.get_service(template.channel)
                    subject = service.render_template(template.subject_template or "", template_vars)
                    content = service.render_template(template.content_template, template_vars)

                    # Create message record
                    message = Message(
                        kol_id=kol.id,
                        campaign_id=campaign_id,
                        subject=subject,
                        content=content,
                        channel=template.channel,
                        recipient=kol.email if template.channel == "email" else kol.social_media_accounts.get(template.channel, {}).get("handle", ""),
                        template_id=message_template_id,
                        template_variables=template_vars,
                        created_by=campaign.created_by
                    )

                    db.add(message)
                    db.flush()  # Get message ID

                    # Send message based on channel
                    send_result = None
                    if template.channel == "email":
                        import asyncio
                        send_result = asyncio.run(send_email(
                            recipient=kol.email,
                            subject=subject,
                            content=content,
                            html=True
                        ))
                    elif template.channel == "discord":
                        discord_id = kol.social_media_accounts.get("discord", {}).get("handle")
                        if discord_id:
                            import asyncio
                            send_result = asyncio.run(send_discord_message(
                                user_id=discord_id,
                                content=content
                            ))

                    # Update message status
                    if send_result and send_result.success:
                        message.status = MessageStatus.SENT
                        message.sent_at = datetime.utcnow()
                        message.provider_message_id = send_result.provider_id
                        results["successful"] += 1
                    else:
                        message.status = MessageStatus.FAILED
                        message.error_message = send_result.error if send_result else "Unknown error"
                        results["failed"] += 1

                    results["messages"].append({
                        "kol_id": kol.id,
                        "kol_name": kol.name,
                        "message_id": message.id,
                        "success": send_result.success if send_result else False,
                        "error": send_result.error if send_result and not send_result.success else None
                    })

                    # Update progress
                    current_task.update_state(
                        state="PROGRESS",
                        meta={
                            "current": i + 1,
                            "total": len(kols),
                            "status": f"Sent to {kol.name}"
                        }
                    )

                except Exception as e:
                    logger.error(f"Failed to send message to KOL {kol.id}: {str(e)}")
                    results["failed"] += 1
                    results["messages"].append({
                        "kol_id": kol.id,
                        "kol_name": kol.name,
                        "success": False,
                        "error": str(e)
                    })

            # Commit all message records
            db.commit()

            logger.info(f"Campaign messaging task {task_id} completed: {results['successful']} sent, {results['failed']} failed")
            return results

        except Exception as e:
            db.rollback()
            logger.error(f"Campaign messaging task {task_id} failed: {str(e)}")
            raise


@celery_app.task
def process_scheduled_messages() -> Dict[str, Any]:
    """
    Process scheduled messages that are due to be sent.

    Returns:
        Dict with processing results
    """
    logger.info("Processing scheduled messages")

    with next(get_db()) as db:
        try:
            # Get messages scheduled for now or earlier
            now = datetime.utcnow()
            scheduled_messages = db.query(Message).filter(
                Message.status == MessageStatus.QUEUED,
                Message.scheduled_for <= now
            ).limit(100).all()  # Process max 100 at a time

            results = {
                "total_processed": len(scheduled_messages),
                "successful": 0,
                "failed": 0,
                "messages": []
            }

            for message in scheduled_messages:
                try:
                    # Send message based on channel
                    send_result = None
                    if message.channel == "email":
                        import asyncio
                        send_result = asyncio.run(send_email(
                            recipient=message.recipient,
                            subject=message.subject,
                            content=message.content,
                            html=True
                        ))
                    elif message.channel == "discord":
                        import asyncio
                        send_result = asyncio.run(send_discord_message(
                            user_id=message.recipient,
                            content=message.content
                        ))
                    elif message.channel == "line":
                        import asyncio
                        send_result = asyncio.run(send_line_message(
                            user_id=message.recipient,
                            content=message.content
                        ))

                    # Update message status
                    if send_result and send_result.success:
                        message.status = MessageStatus.SENT
                        message.sent_at = datetime.utcnow()
                        message.provider_message_id = send_result.provider_id
                        results["successful"] += 1
                    else:
                        message.status = MessageStatus.FAILED
                        message.error_message = send_result.error if send_result else "Unknown error"
                        message.retry_count += 1
                        results["failed"] += 1

                        # Reschedule if retries available
                        if message.can_retry():
                            message.status = MessageStatus.QUEUED
                            message.scheduled_for = datetime.utcnow() + timedelta(minutes=5)  # Retry in 5 minutes

                    results["messages"].append({
                        "message_id": message.id,
                        "recipient": message.recipient,
                        "channel": message.channel,
                        "success": send_result.success if send_result else False
                    })

                except Exception as e:
                    logger.error(f"Failed to send scheduled message {message.id}: {str(e)}")
                    message.status = MessageStatus.FAILED
                    message.error_message = str(e)
                    message.retry_count += 1
                    results["failed"] += 1

            db.commit()

            logger.info(f"Processed {results['total_processed']} scheduled messages: {results['successful']} sent, {results['failed']} failed")
            return results

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to process scheduled messages: {str(e)}")
            raise


@celery_app.task
def process_follow_up_schedules() -> Dict[str, Any]:
    """
    Process follow-up schedules that are due.

    Returns:
        Dict with processing results
    """
    logger.info("Processing follow-up schedules")

    with next(get_db()) as db:
        try:
            # Get schedules that are due
            now = datetime.utcnow()
            due_schedules = db.query(FollowUpSchedule).filter(
                FollowUpSchedule.status == ScheduleStatus.SCHEDULED,
                FollowUpSchedule.scheduled_for <= now
            ).limit(50).all()  # Process max 50 at a time

            results = {
                "total_processed": len(due_schedules),
                "successful": 0,
                "failed": 0,
                "schedules": []
            }

            for schedule in due_schedules:
                try:
                    # Get KOL and template
                    kol = db.query(KOL).filter(KOL.id == schedule.kol_id).first()
                    template = db.query(MessageTemplate).filter(MessageTemplate.id == schedule.message_template_id).first()

                    if not kol or not template:
                        logger.warning(f"KOL or template not found for schedule {schedule.id}")
                        schedule.status = ScheduleStatus.FAILED
                        schedule.execution_notes = "KOL or template not found"
                        results["failed"] += 1
                        continue

                    # Check if we should stop on response
                    if schedule.stop_on_response:
                        # Check if KOL has responded since trigger message
                        recent_response = db.query(Message).filter(
                            Message.kol_id == schedule.kol_id,
                            Message.campaign_id == schedule.campaign_id,
                            Message.response_received == True,
                            Message.created_at > schedule.created_at
                        ).first()

                        if recent_response:
                            schedule.status = ScheduleStatus.CANCELLED
                            schedule.execution_notes = "Cancelled due to KOL response"
                            results["successful"] += 1
                            continue

                    # Prepare template variables
                    template_vars = {
                        "kol_name": kol.name,
                        "trigger_event": schedule.trigger_event,
                    }

                    # Add campaign info if available
                    if schedule.campaign_id:
                        campaign = db.query(Campaign).filter(Campaign.id == schedule.campaign_id).first()
                        if campaign:
                            template_vars.update({
                                "campaign_title": campaign.title,
                                "campaign_description": campaign.description,
                            })

                    # Render message content
                    service = communication_factory.get_service(template.channel)
                    subject = service.render_template(template.subject_template or "", template_vars)
                    content = service.render_template(
                        schedule.custom_message or template.content_template,
                        template_vars
                    )

                    # Create and send message
                    message = Message(
                        kol_id=schedule.kol_id,
                        campaign_id=schedule.campaign_id,
                        subject=subject,
                        content=content,
                        channel=schedule.preferred_channel,
                        recipient=kol.email if schedule.preferred_channel == "email" else
                                  kol.social_media_accounts.get(schedule.preferred_channel, {}).get("handle", ""),
                        template_id=schedule.message_template_id,
                        template_variables=template_vars,
                        tags=["follow_up", schedule.trigger_event]
                    )

                    db.add(message)
                    db.flush()

                    # Send the message
                    send_result = None
                    if schedule.preferred_channel == "email":
                        import asyncio
                        send_result = asyncio.run(send_email(
                            recipient=kol.email,
                            subject=subject,
                            content=content,
                            html=True
                        ))

                    # Update schedules and message status
                    if send_result and send_result.success:
                        message.status = MessageStatus.SENT
                        message.sent_at = datetime.utcnow()
                        message.provider_message_id = send_result.provider_id

                        schedule.status = ScheduleStatus.EXECUTED
                        schedule.executed_at = datetime.utcnow()
                        schedule.executed_message_id = message.id
                        schedule.attempt_count += 1

                        results["successful"] += 1
                    else:
                        message.status = MessageStatus.FAILED
                        message.error_message = send_result.error if send_result else "Unknown error"

                        schedule.attempt_count += 1
                        if schedule.attempt_count >= schedule.max_attempts:
                            schedule.status = ScheduleStatus.FAILED
                            schedule.execution_notes = "Max attempts exceeded"
                        else:
                            # Reschedule for retry
                            schedule.scheduled_for = datetime.utcnow() + timedelta(hours=1)

                        results["failed"] += 1

                    results["schedules"].append({
                        "schedule_id": schedule.id,
                        "kol_id": schedule.kol_id,
                        "trigger_event": schedule.trigger_event,
                        "success": send_result.success if send_result else False
                    })

                except Exception as e:
                    logger.error(f"Failed to process follow-up schedule {schedule.id}: {str(e)}")
                    schedule.status = ScheduleStatus.FAILED
                    schedule.execution_notes = str(e)
                    results["failed"] += 1

            db.commit()

            logger.info(f"Processed {results['total_processed']} follow-up schedules: {results['successful']} executed, {results['failed']} failed")
            return results

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to process follow-up schedules: {str(e)}")
            raise


@priority_task(bind=True)
def send_urgent_message(self, recipient: str, channel: str, subject: str, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Send urgent/priority message immediately.

    Args:
        recipient: Recipient address/ID
        channel: Communication channel
        subject: Message subject
        content: Message content
        metadata: Additional metadata

    Returns:
        Dict with send result
    """
    task_id = self.request.id
    logger.info(f"Sending urgent message via {channel} to {recipient}")

    try:
        # Send message based on channel
        send_result = None
        if channel == "email":
            import asyncio
            send_result = asyncio.run(send_email(
                recipient=recipient,
                subject=subject,
                content=content,
                html=metadata.get("html", False) if metadata else False
            ))
        elif channel == "discord":
            import asyncio
            send_result = asyncio.run(send_discord_message(
                user_id=recipient,
                content=content,
                embed=metadata.get("embed") if metadata else None
            ))
        elif channel == "line":
            import asyncio
            send_result = asyncio.run(send_line_message(
                user_id=recipient,
                content=content
            ))

        return {
            "task_id": task_id,
            "success": send_result.success if send_result else False,
            "message_id": send_result.message_id if send_result else None,
            "provider_id": send_result.provider_id if send_result else None,
            "error": send_result.error if send_result and not send_result.success else None
        }

    except Exception as e:
        logger.error(f"Failed to send urgent message: {str(e)}")
        return {
            "task_id": task_id,
            "success": False,
            "error": str(e)
        }