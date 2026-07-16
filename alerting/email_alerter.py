"""Email-based alerting via SMTP."""

import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from alerting.base import AbstractAlerter

logger = logging.getLogger(__name__)


class EmailAlerter(AbstractAlerter):
    """Send alert emails via SMTP."""

    def __init__(self, config: Dict):
        super().__init__("email")
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.use_tls = config.get('use_tls', True)
        self.username = os.environ.get('SOLO_ROCK_EMAIL_USER') or config.get('username')
        self.password = os.environ.get('SOLO_ROCK_EMAIL_PASS') or config.get('password')
        self.sender = config.get('sender', 'solo-rock@example.com')
        self.recipients = config.get('recipients', [])

        if not self.recipients:
            raise ValueError("Email alerter: no recipients configured")
        if not self.username or not self.password:
            raise ValueError("Email alerter: username/password not configured (set SOLO_ROCK_EMAIL_USER/SOLO_ROCK_EMAIL_PASS env vars)")

    def send_alert(self, event_data: Dict) -> bool:
        """Send alert email, return True if successful."""
        try:
            subject = f"🚨 SOLO ROCK ALERT: CPU Temp {event_data['cpu_temp']:.1f}°C"
            body = self._format_email_body(event_data)

            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = ', '.join(self.recipients)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"[EmailAlerter] Authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"[EmailAlerter] SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"[EmailAlerter] Failed to send email: {e}")
            return False

    def _format_email_body(self, event_data: Dict) -> str:
        """Format alert message body."""
        return f"""
SOLO ROCK EMERGENCY ALERT
========================

Timestamp: {event_data['timestamp']}
Severity: {event_data['severity'].upper()}
Reason: {event_data['reason']}

Current Telemetry:
  CPU Temperature: {event_data['cpu_temp']:.1f}°C
  CPU Load: {event_data['cpu_load']:.1f}%
  RAM Usage: {event_data['ram_usage']:.1f}%
  GPU Load: {event_data['gpu_load']:.1f}%

Action:
  SOLO ROCK has triggered EMERGENCY mode to protect your hardware.
  CPU throttling has been applied to reduce thermal stress.

Next Steps:
  1. Review your workload and shut down non-essential tasks
  2. Check system temperatures with: nvidia-smi (GPU) or sensors (CPU)
  3. Consider adding thermal management (fans, cooling)
  4. Contact your system administrator if this persists

---
SOLO ROCK Hardware Orchestrator
https://github.com/hellomrsys-maker/solo-rock-matrix-engine
"""
