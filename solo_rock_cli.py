#!/usr/bin/env python3
"""
SOLO ROCK CLI — Production-grade command-line interface for the AI orchestrator.

Detects communication protocol issues (retry storms, queue buildup, thermal mismanagement),
measures dispatch reduction under load, and reports exactly what SOLO ROCK is controlling
and what issues it detected in real-time.

Usage:
    python solo_rock_cli.py diagnose      # Detect system communication issues
    python solo_rock_cli.py monitor       # Live telemetry + SOLO ROCK decisions
    python solo_rock_cli.py benchmark     # Run dispatch reduction benchmark
    python solo_rock_cli.py report        # Generate issue report + remediation
"""

import argparse
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from diagnostics.core import DiagnosticsEngine
from monitor_realtime import LiveMonitor
from benchmark_gpu import run_gpu_benchmark, print_report
from report import ReportGenerator


def cmd_diagnose(args):
    """Run system diagnostics to detect communication issues."""
    print("=" * 70)
    print("  SOLO ROCK DIAGNOSTICS — Detecting System Communication Issues")
    print("=" * 70)
    print()

    engine = DiagnosticsEngine()
    issues = engine.run_diagnostics(verbose=args.verbose)

    if not issues:
        print("✓ No critical communication issues detected.")
        return 0

    print(f"⚠ Found {len(issues)} issue(s):\n")
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue['title']}")
        print(f"   Severity: {issue['severity']}")
        print(f"   Details: {issue['description']}")
        if 'remediation' in issue:
            print(f"   Fix: {issue['remediation']}")
        print()

    return 1 if any(i['severity'] == 'critical' for i in issues) else 1


def cmd_monitor(args):
    """Live monitoring of telemetry + SOLO ROCK decisions + issues."""
    print("=" * 70)
    print("  SOLO ROCK LIVE MONITOR — Real-time Orchestration + Issue Detection")
    print("=" * 70)
    print()

    monitor = LiveMonitor(duration_seconds=args.duration, refresh_interval=args.interval)
    try:
        monitor.run()
        return 0
    except KeyboardInterrupt:
        print("\n[Monitor] Stopped by user.")
        return 0


def cmd_benchmark(args):
    """Run dispatch reduction benchmark with real compute workload."""
    print("=" * 70)
    print("  SOLO ROCK GPU BENCHMARK — Proving Dispatch Reduction Under Load")
    print("=" * 70)
    print()

    def on_tick(i, total, snapshot, action, reason, result):
        print(f"[{i+1}/{total}] cpu_load={snapshot['cpu_load']:.1f}% "
              f"cpu_temp={snapshot['cpu_temp']:.1f}C -> {action} | "
              f"compute_result={result:.2e}")

    results = run_gpu_benchmark(
        ticks=args.ticks,
        workload_size=args.workload_size,
        on_tick=on_tick
    )
    print()
    print_report(results)
    return 0


def cmd_report(args):
    """Generate comprehensive issue report + remediation guide."""
    print("=" * 70)
    print("  SOLO ROCK ISSUE REPORT — Global Communication Gap Analysis")
    print("=" * 70)
    print()

    generator = ReportGenerator()
    report = generator.generate()

    if args.format == "json":
        import json
        print(json.dumps(report, indent=2))
    elif args.format == "html":
        html = generator.to_html(report)
        filename = args.output or "solo_rock_report.html"
        with open(filename, 'w') as f:
            f.write(html)
        print(f"Report saved to: {filename}")
    else:  # text/markdown
        print(generator.to_text(report))

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="SOLO ROCK — Production AI Hardware Orchestrator CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python solo_rock_cli.py diagnose              # Detect communication issues
  python solo_rock_cli.py monitor --duration 60 # Monitor for 60 seconds
  python solo_rock_cli.py benchmark --ticks 30  # Run 30-tick benchmark
  python solo_rock_cli.py report --format text  # Generate text report
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # diagnose subcommand
    diag = subparsers.add_parser('diagnose', help='Detect system communication issues')
    diag.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    diag.set_defaults(func=cmd_diagnose)

    # monitor subcommand
    mon = subparsers.add_parser('monitor', help='Live monitoring of orchestration + issues')
    mon.add_argument('--duration', type=int, default=60, help='Monitor duration (seconds)')
    mon.add_argument('--interval', type=float, default=2.0, help='Refresh interval (seconds)')
    mon.set_defaults(func=cmd_monitor)

    # benchmark subcommand
    bench = subparsers.add_parser('benchmark', help='Run dispatch reduction benchmark')
    bench.add_argument('--ticks', type=int, default=20, help='Number of compute iterations')
    bench.add_argument('--workload-size', type=int, default=512, help='GPU matrix size')
    bench.set_defaults(func=cmd_benchmark)

    # report subcommand
    rep = subparsers.add_parser('report', help='Generate issue report + remediation')
    rep.add_argument('--format', choices=['text', 'json', 'html'], default='text',
                     help='Output format')
    rep.add_argument('--output', '-o', help='Output file (for HTML)')
    rep.set_defaults(func=cmd_report)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
