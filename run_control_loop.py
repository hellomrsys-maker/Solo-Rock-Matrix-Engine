"""
Cross-platform, safe-by-default demo of the live Central AI control
loop: real telemetry in, a routing decision out, applied through the
four-node symmetric ring on every tick.

Unlike SOLO_ROCK.py / realtime_boot.py (which assume Windows input/
audio hooks and a display), this script only touches things every
supported platform has: CPU/RAM telemetry via psutil and, on Windows,
optional power-plan control. It is the fastest way for a new
contributor to see the orchestrator actually make decisions.

Usage:
    python run_control_loop.py [--ticks N] [--interval SECONDS]
"""

import argparse
import os
import sys
import time

# A default Windows terminal is often not UTF-8; force it so any non-ASCII
# console output (e.g. a degree sign during an EMERGENCY event) can't crash
# the process with a UnicodeEncodeError.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from central_command.central_ai import CentralAI
from nodes.ai_hub import AiHub, MODE_ORDERS


def main():
    parser = argparse.ArgumentParser(description="SOLO ROCK live control-loop demo")
    parser.add_argument("--ticks", type=int, default=10, help="Number of control cycles to run")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between ticks")
    args = parser.parse_args()

    print("=" * 60)
    print("  SOLO ROCK - LIVE CONTROL LOOP DEMO")
    print("=" * 60)

    ceo = CentralAI()
    hub = AiHub(central_ai=ceo)

    print(f"[Topology] Hardware profile: {ceo.global_state.hardware_profile()}")
    print(f"[Topology] {ceo.global_state.topology}")
    print("-" * 60)

    modes = list(MODE_ORDERS.keys())

    try:
        for i in range(args.ticks):
            action, reason, snapshot = ceo.tick()
            mode = modes[i % len(modes)]
            task = {"task_id": f"demo-task-{i}", "workload_type": "compute", "priority": 1}
            result = hub.dispatch(task, mode=mode)

            print(f"[tick {i+1}/{args.ticks}] cpu_temp={snapshot['cpu_temp']:.1f}C "
                  f"cpu_load={snapshot['cpu_load']:.1f}% ram={snapshot['ram_usage']:.1f}% "
                  f"-> {action} ({reason})")
            print(f"    mode={mode} trace={' -> '.join(result['trace'])} "
                  f"final_action={result['final_action']}")

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[SYSTEM] Control loop stopped by user.")
        return

    print("-" * 60)
    print("  DEMO COMPLETE.")


if __name__ == "__main__":
    main()
