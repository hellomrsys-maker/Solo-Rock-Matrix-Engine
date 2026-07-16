"""Generic webhook alerting via HTTP POST."""

import urllib.request
import json
import os
import logging
from typing import Dict, Optional
from alerting.base import AbstractAlerter

logger = logging.getLogger(__name__)


class WebhookAlerter(AbstractAlerter):
    """Send alerts to custom webhook endpoint via HTTP POST."""

    def __init__(self, config: Dict):
        super().__init__("webhook")
        self.url = config.get('url')
        if not self.url:
            raise ValueError("Webhook alerter: url not configured")
        self.headers = config.get('headers', {})
        # Support env vars in headers (e.g., Authorization: Bearer ${TOKEN})
        for key, value in self.headers.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                self.headers[key] = os.environ.get(env_var, value)

    def send_alert(self, event_data: Dict) -> bool:
        """Send alert to webhook, return True if successful."""
        try:
            payload = self._format_payload(event_data)
            data = json.dumps(payload).encode('utf-8')

            req = urllib.request.Request(
                self.url,
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    **self.headers
                }
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status in (200, 201, 202, 204)
        except urllib.error.HTTPError as e:
            logger.error(f"[WebhookAlerter] HTTP error: {e.code} {e.reason}")
            return False
        except urllib.error.URLError as e:
            logger.error(f"[WebhookAlerter] Network error: {e.reason}")
            return False
        except Exception as e:
            logger.error(f"[WebhookAlerter] Failed to send webhook: {e}")
            return False

    def _format_payload(self, event_data: Dict) -> Dict:
        """Format alert as JSON payload for webhook."""
        return {
            "timestamp": event_data['timestamp'],
            "alert_type": "SOLO_ROCK_EMERGENCY",
            "severity": event_data['severity'],
            "reason": event_data['reason'],
            "telemetry": {
                "cpu_temperature_celsius": event_data['cpu_temp'],
                "cpu_load_percent": event_data['cpu_load'],
                "ram_usage_percent": event_data['ram_usage'],
                "gpu_load_percent": event_data['gpu_load'],
            },
            "action": "Emergency throttling activated to protect hardware",
            "source": "SOLO ROCK Hardware Orchestrator",
        }
