"""
Live Monitor — Real-time view of SOLO ROCK decisions + issues detected.

Shows:
- Current telemetry (CPU temp, load, RAM)
- What SOLO ROCK decided (FULL_RATE/BATCH/THROTTLE/EMERGENCY)
- What issues are detected (retry storm, queue buildup, thermal)
- Rolling 30-second history
"""

import os
import sys
import time
from collections import deque

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from central_command.central_ai import CentralAI
from central_command.decision_engine import FULL_RATE, BATCH, THROTTLE, EMERGENCY
from diagnostics.core import DiagnosticsEngine


class LiveMonitor:
    """Real-time monitoring of orchestration + issue detection."""

    def __init__(self, duration_seconds=60, refresh_interval=2.0):
        self.duration = duration_seconds
        self.refresh_interval = refresh_interval
        self.ceo = CentralAI()
        self.diag_engine = DiagnosticsEngine()
        self.history = deque(maxlen=30)  # 30-second rolling window
        self.decision_counts = {FULL_RATE: 0, BATCH: 0, THROTTLE: 0, EMERGENCY: 0}

    def run(self):
        """Run live monitor for specified duration."""
        start_time = time.time()

        while time.time() - start_time < self.duration:
            # Get current telemetry and decision
            action, reason, snapshot = self.ceo.tick()
            self.history.append({
                'timestamp': time.time(),
                'temp': snapshot.get('cpu_temp', 0.0),
                'load': snapshot.get('cpu_load', 0.0),
                'ram': snapshot.get('ram_usage', 0.0),
                'action': action,
                'reason': reason,
            })
            self.decision_counts[action] += 1

            # Clear screen and draw
            self._draw_screen()

            time.sleep(self.refresh_interval)

        print("\n[Monitor] Complete.")

    def _draw_screen(self):
        """Draw the live monitoring dashboard."""
        # Clear terminal (works on Unix-like systems)
        os.system('clear' if os.name != 'nt' else 'cls')

        if not self.history:
            print("Initializing...")
            return

        latest = self.history[-1]
        avg_temp = sum(h['temp'] for h in self.history) / len(self.history) if self.history else 0
        avg_load = sum(h['load'] for h in self.history) / len(self.history) if self.history else 0
        max_temp = max(h['temp'] for h in self.history) if self.history else 0
        max_load = max(h['load'] for h in self.history) if self.history else 0

        # Header
        print("=" * 75)
        print("  SOLO ROCK LIVE MONITOR — Real-time Orchestration + Issue Detection")
        print("=" * 75)
        print()

        # Current telemetry
        print("CURRENT TELEMETRY:")
        print(f"  CPU Temperature  : {latest['temp']:6.1f}°C  (avg: {avg_temp:.1f}°C, max: {max_temp:.1f}°C)")
        print(f"  CPU Load         : {latest['load']:6.1f}%   (avg: {avg_load:.1f}%, max: {max_load:.1f}%)")
        print(f"  RAM Usage        : {latest['ram']:6.1f}%   ")
        print()

        # Current decision
        decision_colors = {
            FULL_RATE: "🟢 FULL_RATE",
            BATCH: "🔵 BATCH",
            THROTTLE: "🟠 THROTTLE",
            EMERGENCY: "🔴 EMERGENCY",
        }
        print(f"CURRENT DECISION  : {decision_colors.get(latest['action'], latest['action'])}")
        print(f"  Reason          : {latest['reason']}")
        print()

        # Decision statistics
        total = sum(self.decision_counts.values())
        print("DECISION BREAKDOWN (this monitoring session):")
        for action in [FULL_RATE, BATCH, THROTTLE, EMERGENCY]:
            count = self.decision_counts[action]
            pct = (count / total * 100) if total > 0 else 0
            bar_width = int(pct / 2)
            bar = "█" * bar_width + "░" * (50 - bar_width)
            print(f"  {action:<10} : {count:>4} ticks ({pct:>5.1f}%) [{bar}]")
        print()

        # What SOLO ROCK is doing
        print("ORCHESTRATION IMPACT:")
        if self.decision_counts[BATCH] + self.decision_counts[THROTTLE] + self.decision_counts[EMERGENCY] > 0:
            pacing_pct = ((self.decision_counts[BATCH] + self.decision_counts[THROTTLE] + self.decision_counts[EMERGENCY]) / total * 100) if total > 0 else 0
            print(f"  ✓ SOLO ROCK is actively pacing/batching ({pacing_pct:.0f}% of ticks)")
            print(f"  ✓ This reduces redundant hardware submissions")
        else:
            print(f"  ℹ System running at FULL_RATE (workload within headroom)")
        print()

        # Real-time issue detection
        print("REAL-TIME ISSUES:")
        issues = self.diag_engine.run_diagnostics(verbose=False, duration=1)
        if not issues:
            print("  ✓ No communication issues detected")
        else:
            for issue in issues:
                severity_icon = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                }.get(issue.get('severity', 'info'), 'ℹ️')
                print(f"  {severity_icon} {issue['title']} ({issue['severity']})")
                print(f"     {issue['description'][:70]}...")
        print()

        print("=" * 75)
        print(f"[Monitor] Sampling... (press Ctrl+C to stop)")
