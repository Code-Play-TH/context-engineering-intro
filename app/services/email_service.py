"""Email service for sending emails via SMTP."""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
import os
from pathlib import Path
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.default_sender = os.getenv("DEFAULT_SENDER_EMAIL", self.smtp_user)
        self.default_sender_name = os.getenv("DEFAULT_SENDER_NAME", "KOL Management System")

    def send_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        sender_email: Optional[str] = None,
        sender_name: Optional[str] = None,
        is_html: bool = True,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send an email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            content: Email content (HTML or plain text)
            sender_email: Sender email (defaults to configured sender)
            sender_name: Sender name (defaults to configured sender name)
            is_html: Whether content is HTML (default: True)
            attachments: List of attachments with 'filename' and 'content' or 'path'
            cc: List of CC email addresses
            bcc: List of BCC email addresses
            
        Returns:
            Dict with success status and message/error details
        """
        try:
            # Validate configuration
            if not self.smtp_user or not self.smtp_password:
                return {
                    "success": False,
                    "error": "SMTP credentials not configured"
                }

            # Set defaults
            sender_email = sender_email or self.default_sender
            sender_name = sender_name or self.default_sender_name

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{sender_name} <{sender_email}>"
            message["To"] = to_email

            if cc:
                message["Cc"] = ", ".join(cc)

            # Add content
            if is_html:
                html_part = MIMEText(content, "html")
                message.attach(html_part)
            else:
                text_part = MIMEText(content, "plain")
                message.attach(text_part)

            # Add attachments
            if attachments:
                for attachment in attachments:
                    self._add_attachment(message, attachment)

            # Prepare recipient list
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            # Send email
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(sender_email, recipients, message.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return {
                "success": True,
                "message": "Email sent successfully",
                "recipients": recipients
            }

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return {
                "success": False,
                "error": "SMTP authentication failed",
                "details": str(e)
            }

        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"Recipients refused: {e}")
            return {
                "success": False,
                "error": "Recipients refused",
                "details": str(e)
            }

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return {
                "success": False,
                "error": "SMTP error",
                "details": str(e)
            }

        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return {
                "success": False,
                "error": "Unexpected error",
                "details": str(e)
            }

    def _add_attachment(self, message: MIMEMultipart, attachment: Dict[str, Any]):
        """Add an attachment to the email message."""
        try:
            filename = attachment.get("filename", "attachment")
            
            # Handle file path
            if "path" in attachment:
                file_path = Path(attachment["path"])
                if not file_path.exists():
                    logger.warning(f"Attachment file not found: {file_path}")
                    return
                
                with open(file_path, "rb") as f:
                    content = f.read()
            
            # Handle direct content
            elif "content" in attachment:
                content = attachment["content"]
                if isinstance(content, str):
                    content = content.encode("utf-8")
            
            else:
                logger.warning("Attachment missing 'path' or 'content'")
                return

            # Create attachment part
            part = MIMEBase("application", "octet-stream")
            part.set_payload(content)
            encoders.encode_base64(part)
            
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",
            )
            
            message.attach(part)
            logger.debug(f"Added attachment: {filename}")

        except Exception as e:
            logger.error(f"Error adding attachment {filename}: {e}")

    def send_template_email(
        self,
        to_email: str,
        template_content: str,
        template_subject: str,
        variables: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send an email using a template with variable replacement.
        
        Args:
            to_email: Recipient email address
            template_content: Email template content with placeholders
            template_subject: Email subject template with placeholders
            variables: Dictionary of variables to replace in template
            **kwargs: Additional arguments passed to send_email
            
        Returns:
            Dict with success status and message/error details
        """
        try:
            # Replace variables in subject and content
            subject = self._replace_variables(template_subject, variables)
            content = self._replace_variables(template_content, variables)

            return self.send_email(
                to_email=to_email,
                subject=subject,
                content=content,
                **kwargs
            )

        except Exception as e:
            logger.error(f"Error sending template email: {e}")
            return {
                "success": False,
                "error": "Template processing error",
                "details": str(e)
            }

    def _replace_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Replace variables in template string."""
        result = template
        
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        
        return result

    def test_connection(self) -> Dict[str, Any]:
        """Test SMTP connection and authentication."""
        try:
            if not self.smtp_user or not self.smtp_password:
                return {
                    "success": False,
                    "error": "SMTP credentials not configured"
                }

            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                
                server.login(self.smtp_user, self.smtp_password)

            return {
                "success": True,
                "message": "SMTP connection successful"
            }

        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return {
                "success": False,
                "error": "Connection test failed",
                "details": str(e)
            }

    def send_bulk_emails(
        self,
        recipients: List[Dict[str, Any]],
        subject: str,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send bulk emails to multiple recipients.
        
        Args:
            recipients: List of recipient dicts with 'email' and optional 'variables'
            subject: Email subject (can contain variables)
            content: Email content (can contain variables)
            **kwargs: Additional arguments passed to send_email
            
        Returns:
            Dict with success/failure counts and details
        """
        results = {
            "total": len(recipients),
            "success": 0,
            "failed": 0,
            "errors": []
        }

        for recipient in recipients:
            try:
                email = recipient["email"]
                variables = recipient.get("variables", {})
                
                # Replace variables if provided
                final_subject = self._replace_variables(subject, variables)
                final_content = self._replace_variables(content, variables)
                
                result = self.send_email(
                    to_email=email,
                    subject=final_subject,
                    content=final_content,
                    **kwargs
                )
                
                if result["success"]:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "email": email,
                        "error": result["error"]
                    })

            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "email": recipient.get("email", "unknown"),
                    "error": str(e)
                })

        return results