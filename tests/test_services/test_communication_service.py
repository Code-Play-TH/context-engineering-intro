"""
Tests for communication service.

This module contains tests for messaging, notifications,
and communication workflows.
"""

import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from app.services.communication_service import (
    CommunicationService,
    MessageType,
    NotificationChannel
)
from app.models.campaign import Campaign
from app.models.kol import KOL
from app.utils.datetime_utils import get_current_utc
from datetime import timedelta


@pytest.fixture
def db_session():
    """Mock database session fixture."""
    return MagicMock(spec=Session)


@pytest.fixture
def communication_service(db_session):
    """Communication service fixture."""
    return CommunicationService(db_session)


@pytest.fixture
def sample_campaign():
    """Sample campaign fixture."""
    now = get_current_utc()
    return Campaign(
        id=1,
        name="Test Campaign",
        description="Test Description",
        budget=5000.0,
        currency="USD",
        start_date=now + timedelta(days=7),
        end_date=now + timedelta(days=37)
    )


@pytest.fixture
def sample_kol():
    """Sample KOL fixture."""
    return KOL(
        id=1,
        name="Test KOL",
        email="kol@example.com",
        platform="instagram",
        followers_count=50000
    )


class TestDirectMessaging:
    """Tests for direct messaging."""

    def test_send_message_success(self, communication_service):
        """Test sending a direct message."""
        result = communication_service.send_message(
            sender_id=1,
            recipient_id=2,
            subject="Test Message",
            body="This is a test message"
        )

        assert result["success"] is True
        assert "message_id" in result
        assert result["type"] == MessageType.DIRECT

    def test_send_message_with_campaign(self, communication_service):
        """Test sending message with campaign context."""
        result = communication_service.send_message(
            sender_id=1,
            recipient_id=2,
            subject="Campaign Update",
            body="Campaign is live!",
            campaign_id=1
        )

        assert result["success"] is True
        assert "sent_at" in result


class TestBroadcastMessaging:
    """Tests for broadcast messaging."""

    def test_send_broadcast_message(self, communication_service):
        """Test sending broadcast message to multiple recipients."""
        recipient_ids = [1, 2, 3, 4, 5]

        result = communication_service.send_broadcast_message(
            sender_id=1,
            recipient_ids=recipient_ids,
            subject="Important Update",
            body="This is a broadcast message"
        )

        assert result["success"] is True
        assert result["total_recipients"] == 5
        assert result["sent"] == 5
        assert result["failed"] == 0
        assert len(result["message_ids"]) == 5

    def test_send_broadcast_with_campaign(self, communication_service):
        """Test broadcast message with campaign context."""
        result = communication_service.send_broadcast_message(
            sender_id=1,
            recipient_ids=[1, 2, 3],
            subject="Campaign Launch",
            body="Our campaign is now live!",
            campaign_id=1
        )

        assert result["success"] is True
        assert result["sent"] == 3


class TestCampaignInvitations:
    """Tests for campaign invitations."""

    def test_send_campaign_invitation(self, communication_service, db_session, sample_campaign, sample_kol):
        """Test sending campaign invitation to KOL."""
        def mock_query(model):
            mock = MagicMock()
            if model == Campaign:
                mock.filter.return_value.first.return_value = sample_campaign
            elif model == KOL:
                mock.filter.return_value.first.return_value = sample_kol
            return mock

        db_session.query = mock_query

        result = communication_service.send_campaign_invitation(
            campaign_id=1,
            kol_id=1,
            sender_id=1
        )

        assert result["success"] is True
        assert result["type"] == MessageType.CAMPAIGN_INVITE

    def test_send_invitation_with_custom_message(self, communication_service, db_session, sample_campaign, sample_kol):
        """Test campaign invitation with custom message."""
        def mock_query(model):
            mock = MagicMock()
            if model == Campaign:
                mock.filter.return_value.first.return_value = sample_campaign
            elif model == KOL:
                mock.filter.return_value.first.return_value = sample_kol
            return mock

        db_session.query = mock_query

        custom_message = "We think you'd be perfect for this campaign!"

        result = communication_service.send_campaign_invitation(
            campaign_id=1,
            kol_id=1,
            sender_id=1,
            custom_message=custom_message
        )

        assert result["success"] is True

    def test_send_invitation_campaign_not_found(self, communication_service, db_session):
        """Test invitation fails when campaign not found."""
        db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Campaign not found"):
            communication_service.send_campaign_invitation(
                campaign_id=999,
                kol_id=1,
                sender_id=1
            )

    def test_send_invitation_kol_not_found(self, communication_service, db_session, sample_campaign):
        """Test invitation fails when KOL not found."""
        def mock_query(model):
            mock = MagicMock()
            if model == Campaign:
                mock.filter.return_value.first.return_value = sample_campaign
            elif model == KOL:
                mock.filter.return_value.first.return_value = None
            return mock

        db_session.query = mock_query

        with pytest.raises(ValueError, match="KOL not found"):
            communication_service.send_campaign_invitation(
                campaign_id=1,
                kol_id=999,
                sender_id=1
            )


class TestNotifications:
    """Tests for notification system."""

    def test_send_email_notification(self, communication_service):
        """Test sending email notification."""
        result = communication_service.send_notification(
            recipient_id=1,
            title="Test Notification",
            message="This is a test",
            channels=[NotificationChannel.EMAIL]
        )

        assert result["recipient_id"] == 1
        assert NotificationChannel.EMAIL in result["channels_sent"]
        assert result["results"][NotificationChannel.EMAIL]["success"] is True

    def test_send_multi_channel_notification(self, communication_service):
        """Test sending notification through multiple channels."""
        channels = [
            NotificationChannel.EMAIL,
            NotificationChannel.IN_APP,
            NotificationChannel.SMS
        ]

        result = communication_service.send_notification(
            recipient_id=1,
            title="Important Update",
            message="You have a new message",
            channels=channels
        )

        assert len(result["channels_sent"]) == 3
        assert all(result["results"][ch]["success"] for ch in channels)

    def test_send_push_notification(self, communication_service):
        """Test sending push notification."""
        result = communication_service.send_notification(
            recipient_id=1,
            title="New Content",
            message="Content has been approved",
            channels=[NotificationChannel.PUSH]
        )

        assert result["results"][NotificationChannel.PUSH]["success"] is True


class TestContentFeedback:
    """Tests for content feedback messaging."""

    def test_send_approval_feedback(self, communication_service):
        """Test sending content approval feedback."""
        result = communication_service.send_content_feedback(
            content_id=1,
            sender_id=1,
            kol_id=2,
            feedback="Great work! Content approved.",
            is_approved=True
        )

        assert result["success"] is True
        assert result["type"] == MessageType.CONTENT_FEEDBACK

    def test_send_revision_feedback(self, communication_service):
        """Test sending content revision feedback."""
        result = communication_service.send_content_feedback(
            content_id=1,
            sender_id=1,
            kol_id=2,
            feedback="Please adjust the caption and resubmit.",
            is_approved=False
        )

        assert result["success"] is True


class TestReminders:
    """Tests for reminder system."""

    def test_send_deadline_reminder(self, communication_service):
        """Test sending deadline approaching reminder."""
        details = {
            "task_name": "Submit campaign content",
            "due_date": "2025-02-01"
        }

        result = communication_service.send_reminder(
            recipient_id=1,
            reminder_type="deadline_approaching",
            details=details
        )

        assert result["success"] is True
        assert result["type"] == MessageType.REMINDER

    def test_send_content_approval_reminder(self, communication_service):
        """Test sending content pending approval reminder."""
        details = {
            "content_id": 123,
            "submitted_at": "2025-01-15"
        }

        result = communication_service.send_reminder(
            recipient_id=1,
            reminder_type="content_pending_approval",
            details=details
        )

        assert result["success"] is True

    def test_send_payment_reminder(self, communication_service):
        """Test sending payment due reminder."""
        details = {
            "amount": 1500.0,
            "currency": "USD",
            "due_date": "2025-02-15"
        }

        result = communication_service.send_reminder(
            recipient_id=1,
            reminder_type="payment_due",
            details=details
        )

        assert result["success"] is True

    def test_send_custom_reminder(self, communication_service):
        """Test sending custom reminder."""
        details = {
            "message": "Don't forget to check the campaign dashboard!"
        }

        result = communication_service.send_reminder(
            recipient_id=1,
            reminder_type="custom",
            details=details
        )

        assert result["success"] is True


class TestMessageThreading:
    """Tests for message threading."""

    def test_get_message_thread(self, communication_service):
        """Test getting message thread between users."""
        result = communication_service.get_message_thread(
            user_id=1,
            other_user_id=2,
            limit=50
        )

        # Currently returns empty list as it's a placeholder
        assert isinstance(result, list)

    def test_mark_message_as_read(self, communication_service):
        """Test marking message as read."""
        result = communication_service.mark_as_read(
            message_id="msg_123",
            user_id=1
        )

        assert result is True
