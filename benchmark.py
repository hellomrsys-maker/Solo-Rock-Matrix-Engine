"""
SOLO ROCK — Live Benchmark: naive retry-storm vs. orchestrated dispatch.

Answers one question with real numbers from whatever machine runs it:
"how many redundant hardware dispatches does SOLO ROCK avoid?"

Every tick reads real CPU/RAM telemetry (the same call run_control_loop.py
and dashboard.py make) and compares two strategies against that *same*
live data:

  Naive        - what software without an orchestrator does: fire every
                 attempt straight at hardware, whether it's busy or not.
                 Redundant dispatches = every attempt, always.
  SOLO ROCK    - the Decision Engine's real verdict for that tick:
                   FULL_RATE  -> dispatch immediately (1 hit)
                   BATCH      -> coalesce BATCH_COALESCE_FACTOR consecutive
                                 attempts into 1 hit
                   THROTTLE   -> pace THROTTLE_PACE_FACTOR consecutive
                                 attempts down to 1 hit
                   EMERGENCY  -> hold entirely (0 hits) until conditions
                                 normalize

The coalesce/pace factors are this benchmark's illustrative policy
constants, not a universal claim — they exist to make BATCH/HOLD
concrete instead of abstract. The telemetry driving the decision is
always real.

Usage:
    python benchmark.py [--ticks N] [--interval SECONDS]
"""

import argparse
import os
import sys
import time

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from central_command.central_ai import CentralAI
from central_command.decision_engine import FULL_RATE, BATCH, THROTTLE, EMERGENCY

BATCH_COALESCE_FACTOR = 4
THROTTLE_PACE_FACTOR = 3


def run_benchmark(ticks=30, interval=0.3, ceo=None, on_tick=None):
    """
    Drives `ticks` real telemetry samples through the Decision Engine and
    tallies naive vs. SOLO ROCK hardware dispatches. Returns a results dict;
    never touches real hardware controls itself (that's CentralAI.tick()'s
    own EMERGENCY path, unchanged).

    `on_tick(i, ticks, snapshot, action, reason)` is an optional callback,
    e.g. for a progress bar — it receives the same values this function logs.
    """
    ceo = ceo or CentralAI()

    action_counts = {FULL_RATE: 0, BATCH: 0, THROTTLE: 0, EMERGENCY: 0}
    naive_dispatches = 0
    solo_rock_dispatches = 0
    batch_streak = 0
    throttle_streak = 0
    peak_temp = peak_load = peak_ram = 0.0
    ticks_run = []

    for i in range(ticks):
        action, reason, snapshot = ceo.tick()
        action_counts[action] += 1
        peak_temp = max(peak_temp, snapshot.get("cpu_temp", 0.0))
        peak_load = max(peak_load, snapshot.get("cpu_load", 0.0))
        peak_ram = max(peak_ram, snapshot.get("ram_usage", 0.0))

        naive_dispatches += 1  # naive software hits hardware on every attempt, no exceptions

        if action == FULL_RATE:
            solo_rock_dispatches += 1
            batch_streak = throttle_streak = 0
        elif action == BATCH:
            batch_streak += 1
            throttle_streak = 0
            if batch_streak % BATCH_COALESCE_FACTOR == 0:
                solo_rock_dispatches += 1
        elif action == THROTTLE:
            throttle_streak += 1
            batch_streak = 0
            if throttle_streak % THROTTLE_PACE_FACTOR == 0:
                solo_rock_dispatches += 1
        elif action == EMERGENCY:
            batch_streak = throttle_streak = 0
            # held entirely: 0 dispatches while conditions are critical

        ticks_run.append((snapshot, action, reason))
        if on_tick:
            on_tick(i, ticks, snapshot, action, reason)
        if i < ticks - 1:
            time.sleep(interval)

    avoided = naive_dispatches - solo_rock_dispatches
    reduction_pct = (avoided / naive_dispatches * 100.0) if naive_dispatches else 0.0

    return {
        "hardware_profile": ceo.global_state.hardware_profile(),
        "ticks": ticks,
        "action_counts": action_counts,
        "naive_dispatches": naive_dispatches,
        "solo_rock_dispatches": solo_rock_dispatches,
        "avoided_dispatches": avoided,
        "reduction_pct": reduction_pct,
        "peak_cpu_temp": peak_temp,
        "peak_cpu_load": peak_load,
        "peak_ram_usage": peak_ram,
        "ticks_run": ticks_run,
    }


def print_report(results):
    print("=" * 64)
    print("  SOLO ROCK — LIVE BENCHMARK REPORT")
    print("=" * 64)
    print(f"Hardware profile : {results['hardware_profile']}")
    print(f"Ticks sampled    : {results['ticks']}")
    print(f"Peak CPU temp    : {results['peak_cpu_temp']:.1f} C")
    print(f"Peak CPU load    : {results['peak_cpu_load']:.1f} %")
    print(f"Peak RAM usage   : {results['peak_ram_usage']:.1f} %")
    print("-" * 64)
    print("Decision breakdown (real telemetry, real thresholds):")
    for action, count in results["action_counts"].items():
        print(f"    {action:<10} {count:>4} ticks")
    print("-" * 64)
    print(f"Naive dispatches      : {results['naive_dispatches']:>4}  "
          f"(every attempt hits hardware, no exceptions)")
    print(f"SOLO ROCK dispatches  : {results['solo_rock_dispatches']:>4}  "
          f"(coalesced/paced/held per Decision Engine verdict)")
    print(f"Avoided dispatches    : {results['avoided_dispatches']:>4}")
    print(f"Reduction             : {results['reduction_pct']:.1f}%")
    print("=" * 64)
    if results["reduction_pct"] > 0:
        print(f"On this run, SOLO ROCK avoided {results['avoided_dispatches']} redundant "
              f"hardware dispatches ({results['reduction_pct']:.1f}%) using this machine's "
              f"own real telemetry.")
    else:
        print("Hardware stayed fully idle/cool this run — nothing to throttle. Try again "
              "under real load (e.g. run a CPU-heavy task alongside this benchmark) to see "
              "BATCH/THROTTLE kick in.")
    print()


def main():
    parser = argparse.ArgumentParser(description="SOLO ROCK live benchmark: naive vs. orchestrated dispatch")
    parser.add_argument("--ticks", type=int, default=30, help="Number of telemetry samples to take")
    parser.add_argument("--interval", type=float, default=0.3, help="Seconds between samples")
    args = parser.parse_args()

    print("Sampling real telemetry from this machine — this may take a few seconds...\n")

    def on_tick(i, total, snapshot, action, reason):
        print(f"[{i+1}/{total}] cpu_temp={snapshot['cpu_temp']:.1f}C "
              f"cpu_load={snapshot['cpu_load']:.1f}% ram={snapshot['ram_usage']:.1f}% -> {action}")

    results = run_benchmark(ticks=args.ticks, interval=args.interval, on_tick=on_tick)
    print()
    print_report(results)


if __name__ == "__main__":
    main()
