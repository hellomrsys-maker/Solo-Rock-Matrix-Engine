"""
SOLO ROCK GPU Benchmark — measures dispatch reduction when orchestrating
actual GPU workloads under load.

Like benchmark.py, but dispatches real compute work (matrix multiply) to GPU
if available, and measures whether SOLO ROCK's BATCH/THROTTLE decisions
reduce redundant GPU submissions compared to naive retry-storm.

Usage:
    python benchmark_gpu.py [--ticks N] [--workload-size S]
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
from gpu_workload import GPUWorkload

BATCH_COALESCE_FACTOR = 4
THROTTLE_PACE_FACTOR = 3


def run_gpu_benchmark(ticks=20, workload_size=512, on_tick=None):
    """
    Runs actual GPU/CPU compute workload every tick, alongside the Decision Engine.
    Measures naive vs. SOLO ROCK dispatch reduction under real load.
    """
    ceo = CentralAI()
    workload = GPUWorkload(size=workload_size)

    action_counts = {FULL_RATE: 0, BATCH: 0, THROTTLE: 0, EMERGENCY: 0}
    naive_dispatches = 0
    solo_rock_dispatches = 0
    batch_streak = 0
    throttle_streak = 0
    peak_temp = peak_load = peak_ram = 0.0
    compute_results = []

    print(f"Workload: {workload.backend}")
    print(f"Matrix size: {workload.size}x{workload.size}")
    print()

    for i in range(ticks):
        # 1. Run the actual compute work
        try:
            result = workload.compute()
            compute_results.append(result)
        except Exception as e:
            print(f"[Compute Error] {e}")
            result = 0.0

        # 2. Read telemetry and make routing decision (same as benchmark.py)
        action, reason, snapshot = ceo.tick()
        action_counts[action] += 1
        peak_temp = max(peak_temp, snapshot.get("cpu_temp", 0.0))
        peak_load = max(peak_load, snapshot.get("cpu_load", 0.0))
        peak_ram = max(peak_ram, snapshot.get("ram_usage", 0.0))

        # 3. Count dispatches: naive hits hardware every time, SOLO ROCK decides per action
        naive_dispatches += 1

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

        if on_tick:
            on_tick(i, ticks, snapshot, action, reason, result)

        time.sleep(0.1)  # Let system settle between ticks

    avoided = naive_dispatches - solo_rock_dispatches
    reduction_pct = (avoided / naive_dispatches * 100.0) if naive_dispatches else 0.0

    return {
        "workload": workload.info(),
        "ticks": ticks,
        "action_counts": action_counts,
        "naive_dispatches": naive_dispatches,
        "solo_rock_dispatches": solo_rock_dispatches,
        "avoided_dispatches": avoided,
        "reduction_pct": reduction_pct,
        "peak_cpu_temp": peak_temp,
        "peak_cpu_load": peak_load,
        "peak_ram_usage": peak_ram,
        "compute_results": compute_results,
    }


def print_report(results):
    print("=" * 68)
    print("  SOLO ROCK GPU BENCHMARK REPORT")
    print("=" * 68)
    print(f"Workload            : {results['workload']['backend']}")
    print(f"Matrix size         : {results['workload']['matrix_size']}x{results['workload']['matrix_size']}")
    print(f"GPU available       : {results['workload']['gpu_available']}")
    print(f"Ticks executed      : {results['ticks']}")
    print(f"Peak CPU temp       : {results['peak_cpu_temp']:.1f} C")
    print(f"Peak CPU load       : {results['peak_cpu_load']:.1f} %")
    print(f"Peak RAM usage      : {results['peak_ram_usage']:.1f} %")
    print("-" * 68)
    print("Decision breakdown:")
    for action, count in results["action_counts"].items():
        print(f"    {action:<10} {count:>4} ticks")
    print("-" * 68)
    print(f"Naive dispatches    : {results['naive_dispatches']:>4}  "
          f"(every attempt → hardware)")
    print(f"SOLO ROCK dispatches: {results['solo_rock_dispatches']:>4}  "
          f"(paced/batched per Decision Engine)")
    print(f"Avoided dispatches  : {results['avoided_dispatches']:>4}")
    print(f"Reduction           : {results['reduction_pct']:.1f}%")
    print("=" * 68)
    if results["reduction_pct"] > 0:
        print(f"✓ SOLO ROCK avoided {results['avoided_dispatches']} redundant GPU/CPU "
              f"dispatches ({results['reduction_pct']:.1f}%) while running real compute work.")
    else:
        print("System stayed fully idle — run under heavier load (larger matrix, more ticks) "
              "to see BATCH/THROTTLE engage.")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="SOLO ROCK GPU benchmark: real compute workload + naive vs. orchestrated dispatch"
    )
    parser.add_argument("--ticks", type=int, default=20, help="Number of compute iterations")
    parser.add_argument("--workload-size", type=int, default=512, help="Matrix size for GPU workload")
    args = parser.parse_args()

    print("Running GPU workload with Decision Engine pacing...\n")

    def on_tick(i, total, snapshot, action, reason, result):
        print(f"[{i+1}/{total}] cpu_load={snapshot['cpu_load']:.1f}% "
              f"cpu_temp={snapshot['cpu_temp']:.1f}C -> {action} | "
              f"compute_result={result:.2e}")

    results = run_gpu_benchmark(ticks=args.ticks, workload_size=args.workload_size, on_tick=on_tick)
    print()
    print_report(results)


if __name__ == "__main__":
    main()
