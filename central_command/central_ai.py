"""
The Central AI Core (CEO) — final scheduling authority for the whole
Solo Rock matrix. Ties the Global State Vector (telemetry + topology),
the Decision Engine (policy), the Board of Directors (arbitration),
and the Emergency Override (safety reflex) into one control loop that
the Peripheral System's nodes consult before touching hardware.
"""

import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from central_command.global_state_vector import GlobalStateVector
from central_command.decision_engine import DecisionEngine, EMERGENCY
from central_command.board_of_directors import BoardOfDirectors
from central_command.emergency_override import EmergencyOverride
from alerting.base import AlertManager
from infrastructure.event_bus import event_bus

logger = logging.getLogger(__name__)


class CentralAI:
    def __init__(self, config=None):
        self.is_ceo = True
        self.config = config
        self.global_state = GlobalStateVector()
        self.decision_engine = DecisionEngine(config=config)
        self.board = BoardOfDirectors()
        self.emergency = EmergencyOverride()
        self.override_active = False
        self.last_action = None
        self.last_reason = None

        # Initialize alert manager with configuration
        self.alert_manager = AlertManager(config=config if config else {})
        # Subscribe to EMERGENCY events
        event_bus.subscribe("EMERGENCY", self._on_emergency)

    def tick(self):
        """
        One control cycle: refresh telemetry, decide a routing policy,
        and — if things have crossed a critical line — hand off to the
        Emergency Override immediately. Returns (action, reason, snapshot)
        so callers (nodes, demos, tests) can act on the same decision.
        """
        snapshot = self.global_state.sync_from_hardware()
        action, reason = self.decision_engine.decide(snapshot)
        self.last_action, self.last_reason = action, reason

        if action == EMERGENCY and not self.override_active:
            self.override_active = True
            self.emergency.trigger_thermal_shutdown(snapshot.get("cpu_temp", 0.0))
            # Publish EMERGENCY event for alert subscriptions (non-blocking)
            event_bus.publish("EMERGENCY")
        elif action != EMERGENCY and self.override_active:
            # Conditions normalized on their own between ticks; release the override.
            self.emergency.power_ctrl.set_max_processor_state(100)
            self.emergency.is_throttled = False
            self.override_active = False

        return action, reason, snapshot

    def override_all(self):
        """CEO-level manual kill switch: force every department into the safest state."""
        self.override_active = True
        self.emergency.trigger_thermal_shutdown(self.global_state.snapshot().get("cpu_temp", 0.0))
        event_bus.publish("CENTRAL_ESCALATION")

    def release_override(self):
        self.emergency.power_ctrl.set_max_processor_state(100)
        self.emergency.is_throttled = False
        self.override_active = False

    def _on_emergency(self):
        """Callback when EMERGENCY event is published by event bus."""
        snapshot = self.global_state.snapshot() if self.global_state else {}
        self.alert_manager.on_emergency(snapshot=snapshot, reason=self.last_reason)


if __name__ == "__main__":
    ceo = CentralAI()
    print(f"[CentralAI] Hardware profile: {ceo.global_state.hardware_profile()}")
    action, reason, snapshot = ceo.tick()
    print(f"[CentralAI] Decision: {action} ({reason})")
    print(f"[CentralAI] Telemetry: {snapshot}")
