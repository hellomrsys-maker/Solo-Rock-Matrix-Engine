"""Slack-based alerting via webhooks."""

import urllib.request
import json
import os
import logging
from typing import Dict, Optional
from alerting.base import AbstractAlerter

logger = logging.getLogger(__name__)


class SlackAlerter(AbstractAlerter):
    """Send alerts to Slack via incoming webhook."""

    def __init__(self, config: Dict):
        super().__init__("slack")
        self.webhook_url = os.environ.get('SOLO_ROCK_SLACK_WEBHOOK') or config.get('webhook_url')
        if not self.webhook_url:
            raise ValueError("Slack alerter: webhook_url not configured (set SOLO_ROCK_SLACK_WEBHOOK env var or add to config)")
        self.channel = config.get('channel', '#alerts')

    def send_alert(self, event_data: Dict) -> bool:
        """Send alert to Slack, return True if successful."""
        try:
            payload = self._format_slack_message(event_data)
            data = json.dumps(payload).encode('utf-8')

            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200
        except urllib.error.HTTPError as e:
            logger.error(f"[SlackAlerter] HTTP error: {e.code} {e.reason}")
            return False
        except urllib.error.URLError as e:
            logger.error(f"[SlackAlerter] Network error: {e.reason}")
            return False
        except Exception as e:
            logger.error(f"[SlackAlerter] Failed to send Slack message: {e}")
            return False

    def _format_slack_message(self, event_data: Dict) -> Dict:
        """Format alert as Slack message with rich formatting."""
        temp = event_data['cpu_temp']
        load = event_data['cpu_load']
        ram = event_data['ram_usage']

        # Color based on severity
        color = "#CC0000" if event_data['severity'] == 'critical' else "#FF6600"

        return {
            "channel": self.channel,
            "attachments": [
                {
                    "color": color,
                    "title": "🚨 SOLO ROCK EMERGENCY ALERT",
                    "text": event_data['reason'],
                    "fields": [
                        {"title": "CPU Temperature", "value": f"{temp:.1f}°C", "short": True},
                        {"title": "CPU Load", "value": f"{load:.1f}%", "short": True},
                        {"title": "RAM Usage", "value": f"{ram:.1f}%", "short": True},
                        {"title": "GPU Load", "value": f"{event_data['gpu_load']:.1f}%", "short": True},
                        {"title": "Action Taken", "value": "Emergency throttling activated", "short": False},
                    ],
                    "footer": "SOLO ROCK Hardware Orchestrator",
                    "ts": int(event_data['timestamp']),
                }
            ],
        }
