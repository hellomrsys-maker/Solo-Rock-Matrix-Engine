#!/usr/bin/env python3
"""
SOLO ROCK Performance Profiling Suite — measures CLI command latency and resource usage.

Shows:
- Execution time breakdown for each CLI command
- Memory usage (peak and average)
- Decision latency (AMSV read → decision → AMSV write)
- Database overhead
"""

import time
import sys
import os
import subprocess
import psutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class CLIProfiler:
    """Profiles SOLO ROCK CLI commands for performance."""

    def __init__(self):
        self.results = {}

    def profile_command(self, cmd, name=None, count=1):
        """
        Profile a CLI command.

        Args:
            cmd: Command to run (e.g., "python solo_rock_cli.py diagnose")
            name: Display name for the command
            count: Number of iterations to average
        """
        if not name:
            name = cmd.split()[-1]

        print(f"Profiling: {name}")
        times = []
        peak_memory = 0
        avg_memory = 0

        for i in range(count):
            # Start process with memory tracking
            proc = psutil.Process()
            mem_baseline = proc.memory_info().rss / 1024 / 1024  # MB

            start_time = time.time()
            try:
                result = subprocess.run(
                    cmd.split(),
                    capture_output=True,
                    timeout=60,
                    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                elapsed = time.time() - start_time

                # Get peak memory
                peak_mem = proc.memory_info().rss / 1024 / 1024
                memory_used = peak_mem - mem_baseline

                times.append(elapsed)
                peak_memory = max(peak_memory, memory_used)
                avg_memory += memory_used

                print(f"  Run {i+1}/{count}: {elapsed:.2f}s, Memory: {memory_used:.1f}MB")

            except subprocess.TimeoutExpired:
                print(f"  Run {i+1}/{count}: TIMEOUT")
            except Exception as e:
                print(f"  Run {i+1}/{count}: ERROR - {e}")

        if times:
            avg_time = sum(times) / len(times)
            avg_memory = avg_memory / max(len(times), 1)
            self.results[name] = {
                'avg_time': avg_time,
                'min_time': min(times),
                'max_time': max(times),
                'peak_memory_mb': peak_memory,
                'avg_memory_mb': avg_memory,
                'runs': count,
            }
            print(f"  Summary: {avg_time:.2f}s avg, Peak: {peak_memory:.1f}MB")
            print()

    def profile_decision_latency(self, ticks=100):
        """Profile decision engine latency."""
        print(f"Profiling Decision Engine latency ({ticks} ticks)...")
        print()

        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        from central_command.central_ai import CentralAI

        ceo = CentralAI()
        latencies = []

        for i in range(ticks):
            start = time.time()
            action, reason, snapshot = ceo.tick()
            elapsed = (time.time() - start) * 1000  # Convert to ms

            latencies.append(elapsed)

            if (i + 1) % 20 == 0:
                avg_latency = sum(latencies) / len(latencies)
                print(f"  Tick {i+1}/{ticks}: {elapsed:.2f}ms (avg: {avg_latency:.2f}ms)")

        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)

        self.results['decision_latency'] = {
            'avg_ms': avg_latency,
            'min_ms': min_latency,
            'max_ms': max_latency,
            'ticks': ticks,
        }

        print()
        print(f"  Summary:")
        print(f"    - Average: {avg_latency:.2f}ms")
        print(f"    - Min: {min_latency:.2f}ms")
        print(f"    - Max: {max_latency:.2f}ms")
        print()

    def profile_database_overhead(self, operations=1000):
        """Profile database logging overhead."""
        print(f"Profiling Database overhead ({operations} operations)...")
        print()

        from diagnostics.logger import EventLogger

        logger = EventLogger()
        insert_times = []
        query_times = []

        # Profile inserts
        for i in range(operations):
            start = time.time()
            logger.insert_event(
                timestamp=time.time(),
                cpu_temp=50.0,
                cpu_load=50.0,
                ram_usage=50.0,
                decision='FULL_RATE',
                reason='Baseline'
            )
            elapsed = (time.time() - start) * 1000
            insert_times.append(elapsed)

            if (i + 1) % 200 == 0:
                avg_insert = sum(insert_times) / len(insert_times)
                print(f"  Insert {i+1}/{operations}: {elapsed:.3f}ms (avg: {avg_insert:.3f}ms)")

        # Profile queries
        for i in range(10):
            since = time.time() - (i + 1) * 60
            start = time.time()
            events = logger.get_events_since(since)
            elapsed = (time.time() - start) * 1000
            query_times.append(elapsed)
            print(f"  Query {i+1}/10: {elapsed:.3f}ms ({len(events)} events)")

        avg_insert = sum(insert_times) / len(insert_times)
        avg_query = sum(query_times) / len(query_times)

        self.results['database_overhead'] = {
            'insert_avg_ms': avg_insert,
            'insert_min_ms': min(insert_times),
            'insert_max_ms': max(insert_times),
            'query_avg_ms': avg_query,
            'query_min_ms': min(query_times),
            'query_max_ms': max(query_times),
            'operations': operations,
        }

        print()
        print(f"  Summary:")
        print(f"    - Insert: {avg_insert:.3f}ms avg")
        print(f"    - Query: {avg_query:.3f}ms avg")
        print()

    def print_summary(self):
        """Print profiling results summary."""
        print()
        print("=" * 70)
        print("  PERFORMANCE PROFILING RESULTS")
        print("=" * 70)
        print()

        for name, metrics in self.results.items():
            print(f"📊 {name}")
            for key, value in metrics.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.2f}")
                else:
                    print(f"  {key}: {value}")
            print()

        # Recommendations
        print("📋 Recommendations:")
        print()

        # Check CLI latency
        if 'diagnose' in self.results:
            diagnose_time = self.results['diagnose'].get('avg_time', 0)
            if diagnose_time > 5:
                print(f"  ⚠️  diagnose is slow ({diagnose_time:.1f}s) — consider optimizing diagnostics")
            else:
                print(f"  ✓ diagnose is fast ({diagnose_time:.1f}s)")

        # Check decision latency
        if 'decision_latency' in self.results:
            avg_latency = self.results['decision_latency'].get('avg_ms', 0)
            if avg_latency > 10:
                print(f"  ⚠️  Decision latency is high ({avg_latency:.2f}ms) — may impact responsiveness")
            else:
                print(f"  ✓ Decision latency is excellent ({avg_latency:.2f}ms)")

        # Check database overhead
        if 'database_overhead' in self.results:
            insert_time = self.results['database_overhead'].get('insert_avg_ms', 0)
            if insert_time > 1:
                print(f"  ⚠️  Database inserts are slow ({insert_time:.3f}ms) — may bottleneck logging")
            else:
                print(f"  ✓ Database inserts are fast ({insert_time:.3f}ms)")

        print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="SOLO ROCK CLI Performance Profiler"
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Profile everything (default if no args)'
    )
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Profile CLI commands'
    )
    parser.add_argument(
        '--decision',
        action='store_true',
        help='Profile decision engine latency'
    )
    parser.add_argument(
        '--database',
        action='store_true',
        help='Profile database overhead'
    )
    parser.add_argument(
        '--ticks',
        type=int,
        default=100,
        help='Number of decision ticks to profile (default 100)'
    )

    args = parser.parse_args()

    # Default to --all if nothing specified
    if not (args.cli or args.decision or args.database):
        args.all = True

    profiler = CLIProfiler()

    print("=" * 70)
    print("  SOLO ROCK PERFORMANCE PROFILER")
    print("=" * 70)
    print()

    if args.cli or args.all:
        profiler.profile_command("python solo_rock_cli.py diagnose", "diagnose", count=1)

    if args.decision or args.all:
        profiler.profile_decision_latency(ticks=args.ticks)

    if args.database or args.all:
        profiler.profile_database_overhead(operations=500)

    profiler.print_summary()
    return 0


if __name__ == '__main__':
    exit(main())
