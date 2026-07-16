#!/usr/bin/env python3
"""
SOLO ROCK Auto-Calibration Tool — Measures baseline system behavior and suggests optimal thresholds.

Run on idle system (1 hour baseline scan) to generate calibration.json with per-hardware tuned values.
"""

import os
import sys
import time
import json
import statistics
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from central_command.central_ai import CentralAI
from diagnostics.logger import EventLogger
from analytics.query import TelemetryAnalyzer


class SystemCalibrator:
    """Analyzes baseline system state and suggests optimal thresholds."""

    def __init__(self):
        self.baseline_temps = []
        self.baseline_loads = []
        self.baseline_ram = []
        self.logger = EventLogger()
        self.ceo = CentralAI()
        self.sample_count = 0
        self.start_time = None

    def collect_baseline(self, duration_seconds=3600, interval=2.0):
        """
        Collect baseline telemetry on idle system.

        Args:
            duration_seconds: How long to sample (default 1 hour)
            interval: Sample interval in seconds (default 2 seconds)
        """
        print("=" * 70)
        print("  SOLO ROCK Auto-Calibration Tool")
        print("=" * 70)
        print()
        print("⚠️  This tool should be run on an IDLE system (no heavy workloads)")
        print(f"⏱️  Collecting baseline for {duration_seconds // 60} minutes...")
        print()
        print("Sampling telemetry...")
        print()

        self.start_time = time.time()
        self.sample_count = 0

        try:
            while time.time() - self.start_time < duration_seconds:
                # Get current state
                action, reason, snapshot = self.ceo.tick()

                # Record telemetry
                cpu_temp = snapshot.get('cpu_temp', 0.0)
                cpu_load = snapshot.get('cpu_load', 0.0)
                ram_usage = snapshot.get('ram_usage', 0.0)

                self.baseline_temps.append(cpu_temp)
                self.baseline_loads.append(cpu_load)
                self.baseline_ram.append(ram_usage)

                # Log to database
                current_time = time.time()
                self.logger.insert_event(
                    timestamp=current_time,
                    cpu_temp=cpu_temp,
                    cpu_load=cpu_load,
                    ram_usage=ram_usage,
                    gpu_load=snapshot.get('gpu_load', 0.0),
                    decision=action,
                    reason=reason,
                    action_taken=action
                )

                self.sample_count += 1

                # Progress indicator
                if self.sample_count % 30 == 0:
                    elapsed = int(time.time() - self.start_time)
                    progress = (elapsed / duration_seconds) * 100
                    print(f"  [{progress:5.1f}%] Samples: {self.sample_count}, "
                          f"Temp: {cpu_temp:.1f}°C, Load: {cpu_load:.1f}%, RAM: {ram_usage:.1f}%")

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n⚠️  Calibration interrupted by user")
            return False

        print()
        print(f"✓ Collected {self.sample_count} samples")
        return True

    def analyze_baseline(self) -> dict:
        """Analyze collected baseline and suggest thresholds."""
        print()
        print("Analyzing baseline telemetry...")
        print()

        if len(self.baseline_temps) == 0:
            print("❌ No baseline data collected")
            return {}

        # Calculate statistics
        temp_avg = statistics.mean(self.baseline_temps)
        temp_max = max(self.baseline_temps)
        temp_min = min(self.baseline_temps)
        temp_stdev = statistics.stdev(self.baseline_temps) if len(self.baseline_temps) > 1 else 0

        load_avg = statistics.mean(self.baseline_loads)
        load_max = max(self.baseline_loads)
        load_min = min(self.baseline_loads)
        load_stdev = statistics.stdev(self.baseline_loads) if len(self.baseline_loads) > 1 else 0

        ram_avg = statistics.mean(self.baseline_ram)
        ram_max = max(self.baseline_ram)
        ram_min = min(self.baseline_ram)

        print("📊 Baseline Statistics:")
        print()
        print(f"  CPU Temperature:")
        print(f"    - Average: {temp_avg:.1f}°C")
        print(f"    - Min: {temp_min:.1f}°C, Max: {temp_max:.1f}°C")
        print(f"    - Std Dev: {temp_stdev:.1f}°C")
        print()
        print(f"  CPU Load:")
        print(f"    - Average: {load_avg:.1f}%")
        print(f"    - Min: {load_min:.1f}%, Max: {load_max:.1f}%")
        print(f"    - Std Dev: {load_stdev:.1f}%")
        print()
        print(f"  RAM Usage:")
        print(f"    - Average: {ram_avg:.1f}%")
        print(f"    - Min: {ram_min:.1f}%, Max: {ram_max:.1f}%")
        print()

        # Suggest thresholds based on percentiles
        temps_sorted = sorted(self.baseline_temps)
        loads_sorted = sorted(self.baseline_loads)

        # 70th percentile for warning (some headroom but not excessive)
        idx_70 = int(len(temps_sorted) * 0.70)
        temp_70 = temps_sorted[idx_70] if idx_70 < len(temps_sorted) else temp_avg

        # 85th percentile for high load
        idx_85 = int(len(loads_sorted) * 0.85)
        load_85 = loads_sorted[idx_85] if idx_85 < len(loads_sorted) else load_avg

        # 95th percentile for critical
        idx_95_temp = int(len(temps_sorted) * 0.95)
        idx_95_load = int(len(loads_sorted) * 0.95)
        temp_95 = temps_sorted[idx_95_temp] if idx_95_temp < len(temps_sorted) else temp_avg
        load_95 = loads_sorted[idx_95_load] if idx_95_load < len(loads_sorted) else load_avg

        # Generate suggested thresholds
        # Add safety margins (round up)
        suggested_thermal_warning = round(temp_70 + 5)  # 70th percentile + 5°C buffer
        suggested_thermal_critical = round(temp_95 + 5)  # 95th percentile + 5°C buffer
        suggested_thermal_throttle = round(temp_70)      # Start pacing at 70th percentile

        suggested_cpu_high = round(load_85 + 5)         # 85th percentile + 5% buffer
        suggested_cpu_critical = round(load_95 + 5)     # 95th percentile + 5% buffer

        # RAM: use high percentile, keep conservative
        ram_max_safe = round(ram_max + 2)  # Max observed + 2%
        suggested_ram_critical = max(95, ram_max_safe)   # At least 95%, but allow system headroom

        print("💡 Suggested Thresholds (with safety margins):")
        print()
        print(f"  thermal:")
        print(f"    warning_celsius: {suggested_thermal_warning}")
        print(f"    critical_celsius: {suggested_thermal_critical}")
        print(f"    throttle_threshold: {suggested_thermal_throttle}")
        print()
        print(f"  cpu:")
        print(f"    load_high_percent: {suggested_cpu_high}")
        print(f"    load_critical_percent: {suggested_cpu_critical}")
        print()
        print(f"  ram:")
        print(f"    critical_percent: {suggested_ram_critical}")
        print()

        # Validate thresholds
        if suggested_thermal_critical <= suggested_thermal_warning:
            print("⚠️  Warning: Critical temperature ≤ Warning temperature. Adjusting...")
            suggested_thermal_critical = suggested_thermal_warning + 5

        if suggested_cpu_critical <= suggested_cpu_high:
            print("⚠️  Warning: Critical CPU load ≤ High load. Adjusting...")
            suggested_cpu_critical = suggested_cpu_high + 5

        return {
            'thermal': {
                'warning_celsius': suggested_thermal_warning,
                'critical_celsius': suggested_thermal_critical,
                'throttle_threshold': suggested_thermal_throttle,
            },
            'cpu': {
                'load_high_percent': suggested_cpu_high,
                'load_critical_percent': suggested_cpu_critical,
            },
            'ram': {
                'critical_percent': suggested_ram_critical,
            },
            'baseline': {
                'sample_count': self.sample_count,
                'duration_seconds': int(time.time() - self.start_time),
                'temperature': {
                    'avg': round(temp_avg, 1),
                    'min': round(temp_min, 1),
                    'max': round(temp_max, 1),
                    'stdev': round(temp_stdev, 1),
                },
                'cpu_load': {
                    'avg': round(load_avg, 1),
                    'min': round(load_min, 1),
                    'max': round(load_max, 1),
                    'stdev': round(load_stdev, 1),
                },
                'ram_usage': {
                    'avg': round(ram_avg, 1),
                    'min': round(ram_min, 1),
                    'max': round(ram_max, 1),
                },
                'timestamp': datetime.now().isoformat(),
            }
        }

    def save_calibration(self, calibration_data: dict):
        """Save calibration to calibration.json."""
        calib_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'config',
            'calibration.json'
        )

        try:
            os.makedirs(os.path.dirname(calib_path), exist_ok=True)
            with open(calib_path, 'w') as f:
                json.dump(calibration_data, f, indent=2)
            print(f"✓ Calibration saved to: {calib_path}")
            print()
            return True
        except Exception as e:
            print(f"❌ Failed to save calibration: {e}")
            return False


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="SOLO ROCK Auto-Calibration Tool — measure baseline and suggest thresholds"
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=3600,
        help='Baseline collection duration in seconds (default 3600 = 1 hour)'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=2.0,
        help='Sample interval in seconds (default 2.0)'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save calibration to calibration.json'
    )

    args = parser.parse_args()

    calibrator = SystemCalibrator()

    # Collect baseline
    if not calibrator.collect_baseline(
        duration_seconds=args.duration,
        interval=args.interval
    ):
        return 1

    # Analyze and suggest thresholds
    calibration = calibrator.analyze_baseline()

    if not calibration:
        return 1

    # Save calibration
    if not args.no_save:
        if not calibrator.save_calibration(calibration):
            return 1
        print("Next steps:")
        print("  1. Review calibration.json to verify suggested thresholds")
        print("  2. Adjust if needed based on your workload characteristics")
        print("  3. Restart SOLO ROCK to apply calibrated thresholds")
    else:
        print("(Calibration not saved; use without --no-save to save)")

    return 0


if __name__ == '__main__':
    exit(main())
