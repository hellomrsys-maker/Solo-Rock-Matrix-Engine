"""Base alerter classes and alert manager orchestration."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import time

logger = logging.getLogger(__name__)


class AbstractAlerter(ABC):
    """Base class for alert backends (email, Slack, webhooks, etc.)."""

    def __init__(self, name: str):
        self.name = name
        self.last_alert_time = 0
        self.min_alert_interval = 60  # Throttle: max 1 alert per minute per backend

    @abstractmethod
    def send_alert(self, event_data: Dict) -> bool:
        """
        Send alert, return True if successful.

        event_data contains:
        - timestamp: Unix timestamp
        - cpu_temp: CPU temperature in Celsius
        - cpu_load: CPU load percentage (0-100)
        - ram_usage: RAM usage percentage (0-100)
        - reason: Decision engine reason for EMERGENCY
        - severity: 'critical' or 'high'
        """
        pass

    def should_throttle(self) -> bool:
        """Check if alert should be throttled (avoid spam)."""
        now = time.time()
        if now - self.last_alert_time < self.min_alert_interval:
            return True
        self.last_alert_time = now
        return False


class AlertManager:
    """Orchestrates multiple alert backends, subscribes to EMERGENCY events."""

    def __init__(self, config: Optional[Dict] = None):
        # Handle both SoloRockConfig objects and plain dicts
        if hasattr(config, 'get_all'):
            # It's a SoloRockConfig object
            self.config = config.get_all()
        elif hasattr(config, 'get') and callable(config.get):
            # It's a dict-like object with get method
            self.config = config
        else:
            # It's a plain dict or None
            self.config = config or {}

        self.alerters: List[AbstractAlerter] = []
        alerting_cfg = self.config.get('alerting', {})
        self.enabled = alerting_cfg.get('enabled', True)
        self.latest_snapshot = None
        self.latest_reason = None
        self._initialize_backends()

    def _initialize_backends(self):
        """Initialize alerters from configuration."""
        if not self.enabled:
            logger.info("[AlertManager] Alerting disabled in configuration")
            return

        alerting_cfg = self.config.get('alerting', {})
        if not alerting_cfg:
            logger.info("[AlertManager] No alerting configuration found")
            return

        backends_config = alerting_cfg.get('backends', [])
        if not backends_config:
            logger.info("[AlertManager] No alert backends configured")
            return

        for backend_cfg in backends_config:
            backend_type = backend_cfg.get('type')

            if backend_type == 'email':
                try:
                    from alerting.email_alerter import EmailAlerter
                    alerter = EmailAlerter(config=backend_cfg)
                    self.alerters.append(alerter)
                    logger.info(f"[AlertManager] Initialized email alerter: {backend_cfg.get('sender')}")
                except Exception as e:
                    logger.warning(f"[AlertManager] Failed to initialize email alerter: {e}")

            elif backend_type == 'slack':
                try:
                    from alerting.slack_alerter import SlackAlerter
                    alerter = SlackAlerter(config=backend_cfg)
                    self.alerters.append(alerter)
                    logger.info(f"[AlertManager] Initialized Slack alerter")
                except Exception as e:
                    logger.warning(f"[AlertManager] Failed to initialize Slack alerter: {e}")

            elif backend_type == 'webhook':
                try:
                    from alerting.webhook_alerter import WebhookAlerter
                    alerter = WebhookAlerter(config=backend_cfg)
                    self.alerters.append(alerter)
                    logger.info(f"[AlertManager] Initialized webhook alerter: {backend_cfg.get('url')}")
                except Exception as e:
                    logger.warning(f"[AlertManager] Failed to initialize webhook alerter: {e}")

    def on_emergency(self, snapshot: Optional[Dict] = None, reason: str = "EMERGENCY condition"):
        """Called when EMERGENCY event is published by event bus."""
        if not self.enabled or not self.alerters:
            return

        self.latest_snapshot = snapshot or {}
        self.latest_reason = reason

        event_data = {
            'timestamp': time.time(),
            'cpu_temp': snapshot.get('cpu_temp', 0.0) if snapshot else 0.0,
            'cpu_load': snapshot.get('cpu_load', 0.0) if snapshot else 0.0,
            'ram_usage': snapshot.get('ram_usage', 0.0) if snapshot else 0.0,
            'gpu_load': snapshot.get('gpu_load', 0.0) if snapshot else 0.0,
            'reason': reason,
            'severity': 'critical',
        }

        for alerter in self.alerters:
            if alerter.should_throttle():
                logger.debug(f"[AlertManager] Throttling {alerter.name} (too many recent alerts)")
                continue

            try:
                success = alerter.send_alert(event_data)
                if success:
                    logger.info(f"[AlertManager] Alert sent via {alerter.name}")
                else:
                    logger.warning(f"[AlertManager] Alert failed via {alerter.name}")
            except Exception as e:
                logger.error(f"[AlertManager] Exception in {alerter.name}: {e}")

    def send_test_alert(self):
        """Send a test alert to all backends (for validation)."""
        logger.info("[AlertManager] Sending test alert to all backends")
        event_data = {
            'timestamp': time.time(),
            'cpu_temp': 85.0,
            'cpu_load': 80.0,
            'ram_usage': 95.0,
            'gpu_load': 70.0,
            'reason': '[TEST] This is a test alert from SOLO ROCK',
            'severity': 'high',
        }

        for alerter in self.alerters:
            try:
                success = alerter.send_alert(event_data)
                if success:
                    logger.info(f"[AlertManager] Test alert sent via {alerter.name}")
                else:
                    logger.warning(f"[AlertManager] Test alert failed via {alerter.name}")
            except Exception as e:
                logger.error(f"[AlertManager] Exception in test alert ({alerter.name}): {e}")
