"""
DiagnosticsEngine — Detects software→hardware communication issues in real-time.

The core problem: Software has no way to tell hardware "I'm busy, slow down."
Result: retry storms, queue buildup, thermal spikes, wasted capacity.

This engine detects each problem pattern and rates severity.
"""

import os
import sys
import time
import psutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hardware_drivers.topology import HardwareTopology
from hardware_drivers.hardware_reader import HardwareReader
from central_command.decision_engine import DecisionEngine, FULL_RATE, BATCH, THROTTLE, EMERGENCY


class DiagnosticsEngine:
    """Detects communication protocol issues between software and hardware."""

    def __init__(self):
        self.topo = HardwareTopology()
        self.hw_reader = HardwareReader()
        self.decision_engine = DecisionEngine()
        self.issues = []

    def run_diagnostics(self, verbose=False, duration=5):
        """
        Run full diagnostics: sample telemetry, detect issues, return findings.
        """
        self.issues = []

        if verbose:
            print(f"Scanning system for 5 seconds...\n")

        snapshots = []
        peak_temp = peak_load = peak_ram = 0.0
        decisions = {FULL_RATE: 0, BATCH: 0, THROTTLE: 0, EMERGENCY: 0}
        retry_spike_count = 0
        last_cpu_load = None

        # Sample telemetry over duration
        start = time.time()
        while time.time() - start < duration:
            try:
                snapshot = self.hw_reader.get_telemetry_snapshot()
                snapshots.append(snapshot)

                cpu_temp = snapshot.get("cpu_temp", 0.0)
                cpu_load = snapshot.get("cpu_load", 0.0)
                ram_usage = snapshot.get("ram_usage", 0.0)

                peak_temp = max(peak_temp, cpu_temp)
                peak_load = max(peak_load, cpu_load)
                peak_ram = max(peak_ram, ram_usage)

                # Detect sudden load spikes (sign of retry storm)
                if last_cpu_load is not None and cpu_load - last_cpu_load > 30:
                    retry_spike_count += 1

                # What decision would the engine make?
                action, _ = self.decision_engine.decide(snapshot)
                decisions[action] += 1

                last_cpu_load = cpu_load

                if verbose:
                    print(f"  temp={cpu_temp:.1f}C load={cpu_load:.1f}% ram={ram_usage:.1f}% -> {action}")

                time.sleep(0.5)
            except Exception as e:
                if verbose:
                    print(f"  [Error sampling] {e}")

        if verbose:
            print()

        # Analyze the snapshots for issues
        self._detect_retry_storms(snapshots, decisions, verbose)
        self._detect_thermal_mismanagement(peak_temp, peak_load, retry_spike_count, verbose)
        self._detect_backpressure_breakdown(decisions, verbose)
        self._detect_queue_issues(snapshots, verbose)

        return self.issues

    def _detect_retry_storms(self, snapshots, decisions, verbose):
        """Detect if software is retrying excessively."""
        if not snapshots:
            return

        # Signs of retry storm:
        # 1. Frequent FULL_RATE (no back-pressure) even under load
        # 2. Sudden CPU load spikes without matching task submission
        # 3. High CPU load % but low actual work throughput

        full_rate_pct = (decisions.get(FULL_RATE, 0) / len(snapshots) * 100) if snapshots else 0
        batch_throttle_pct = (decisions.get(BATCH, 0) + decisions.get(THROTTLE, 0)) / len(snapshots) * 100

        avg_load = sum(s.get("cpu_load", 0) for s in snapshots) / len(snapshots) if snapshots else 0

        if full_rate_pct > 70 and avg_load > 60:
            self.issues.append({
                "title": "Retry Storm Detected",
                "severity": "high",
                "description": (
                    f"System stayed in FULL_RATE mode {full_rate_pct:.0f}% of the time despite "
                    f"average CPU load of {avg_load:.0f}%. This suggests software is firing commands "
                    f"at hardware without waiting for completion, typical of retry-on-timeout loops."
                ),
                "remediation": (
                    "1. Add exponential backoff to retry logic (don't retry immediately)\n"
                    "2. Increase timeout thresholds so hardware has time to respond\n"
                    "3. Enable SOLO ROCK's BATCH mode to coalesce redundant submissions"
                ),
            })
            if verbose:
                print(f"[Retry Storm] FULL_RATE={full_rate_pct:.0f}%, avg_load={avg_load:.0f}%")

    def _detect_thermal_mismanagement(self, peak_temp, peak_load, spike_count, verbose):
        """Detect if thermal spikes are caused by redundant load, not real workload."""
        from central_command.decision_engine import THERMAL_WARNING_C, THERMAL_CRITICAL_C

        if peak_temp > THERMAL_WARNING_C:
            severity = "critical" if peak_temp > THERMAL_CRITICAL_C else "high"
            self.issues.append({
                "title": "Thermal Escalation Risk",
                "severity": severity,
                "description": (
                    f"Peak temperature reached {peak_temp:.1f}°C (threshold: {THERMAL_WARNING_C}°C). "
                    f"If this is caused by retry storms rather than legitimate high load, "
                    f"reducing redundant submissions will cool the system significantly."
                ),
                "remediation": (
                    "1. Run SOLO ROCK with active thermal throttling enabled\n"
                    "2. Reduce application retry frequency\n"
                    "3. Monitor if temperature drops when dispatch reduction is active"
                ),
            })
            if verbose:
                print(f"[Thermal] Peak {peak_temp:.1f}°C, spike_events={spike_count}")

    def _detect_backpressure_breakdown(self, decisions, verbose):
        """Detect if software keeps sending when hardware is busy."""
        total_decisions = sum(decisions.values())
        if total_decisions == 0:
            return

        batch_throttle_emergency = decisions.get(BATCH, 0) + decisions.get(THROTTLE, 0) + decisions.get(EMERGENCY, 0)
        pacing_pct = (batch_throttle_emergency / total_decisions * 100) if total_decisions else 0

        if pacing_pct < 10 and decisions.get(FULL_RATE, 0) > total_decisions * 0.9:
            self.issues.append({
                "title": "Backpressure Not Engaged",
                "severity": "medium",
                "description": (
                    f"System remained in FULL_RATE mode {100 - pacing_pct:.0f}% of the time. "
                    f"BATCH/THROTTLE modes (which provide backpressure) were never triggered. "
                    f"This either means: (1) workload is genuinely light, or (2) software has "
                    f"no mechanism to respond to hardware being busy."
                ),
                "remediation": (
                    "1. Enable SOLO ROCK monitoring to detect when backpressure should engage\n"
                    "2. Verify Decision Engine thresholds match your hardware (may be set too high)\n"
                    "3. Run under realistic load to trigger BATCH/THROTTLE scenarios"
                ),
            })
            if verbose:
                print(f"[Backpressure] Pacing engaged {pacing_pct:.0f}% of time")

    def _detect_queue_issues(self, snapshots, verbose):
        """Detect queue buildup or high memory use (indirect queue indicator)."""
        if not snapshots:
            return

        avg_ram = sum(s.get("ram_usage", 0) for s in snapshots) / len(snapshots)
        max_ram = max(s.get("ram_usage", 0) for s in snapshots)

        if max_ram > 85:
            self.issues.append({
                "title": "High Memory Usage (Possible Queue Buildup)",
                "severity": "medium",
                "description": (
                    f"RAM usage peaked at {max_ram:.0f}%. This can indicate command queue buildup "
                    f"if software is submitting faster than hardware can process. "
                    f"Backpressure should prevent queue from growing unbounded."
                ),
                "remediation": (
                    "1. Monitor queue depth in hardware driver (nvidia-smi for GPU)\n"
                    "2. Reduce software submission rate or enable SOLO ROCK pacing\n"
                    "3. Profile which components are consuming the memory"
                ),
            })
            if verbose:
                print(f"[Memory] Peak {max_ram:.0f}%, avg {avg_ram:.0f}%")
