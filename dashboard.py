"""
SOLO ROCK — Live Control Loop Dashboard (Streamlit)

A visual front end for the Central AI control loop implemented in
central_command/ and nodes/: real hardware telemetry in, a routing
decision out, applied through the four-node symmetric ring.

Two modes:
  - Live mode:       reads real CPU/RAM telemetry via CentralAI.tick().
                      On Windows with an administrator shell, an
                      EMERGENCY reading will trigger the real
                      EmergencyOverride (power-plan throttle). Everywhere
                      else this stays telemetry-only, exactly as the
                      engine itself does.
  - Simulation mode: overrides telemetry with slider values so anyone
                      can demo THROTTLE/EMERGENCY behavior without a
                      genuinely hot CPU. This path never touches real
                      hardware controls — it only computes what the
                      Decision Engine *would* decide.

Run with:
    streamlit run dashboard.py
"""

import os
import sys
import time

# Some imported modules print non-ASCII characters (e.g. a degree sign) on
# console output. A default Windows terminal often isn't UTF-8, which turns
# that into a crash (UnicodeEncodeError) the moment such a line prints —
# most visibly right when an EMERGENCY event fires. Force UTF-8 first.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from central_command.central_ai import CentralAI
from central_command.decision_engine import (
    CPU_LOAD_HIGH_PCT,
    CPU_LOAD_MODERATE_PCT,
    RAM_CRITICAL_PCT,
    THERMAL_CRITICAL_C,
    THERMAL_WARNING_C,
)
from nodes.ai_hub import AiHub, MODE_ORDERS

st.set_page_config(page_title="SOLO ROCK Control Loop", page_icon="🧠", layout="wide")

ACTION_STYLE = {
    "FULL_RATE": ("success", "🟢"),
    "BATCH": ("info", "🔵"),
    "THROTTLE": ("warning", "🟠"),
    "EMERGENCY": ("error", "🔴"),
}
FINAL_ACTION_ICON = {
    "DISPATCH": "✅ DISPATCH",
    "DISPATCH_BATCHED": "📦 DISPATCH_BATCHED",
    "HOLD": "⏸️ HOLD",
    "REJECT": "⛔ REJECT",
}


def render_action_box(action, reason, simulated=False):
    style, icon = ACTION_STYLE.get(action, ("info", "❔"))
    label = f"{icon} **{action}** — {reason}"
    if simulated:
        label += "  \n*(simulated telemetry — no real hardware changes made)*"
    getattr(st, style)(label)


def init_state():
    if "ceo" not in st.session_state:
        st.session_state.ceo = CentralAI()
    if "hub_live" not in st.session_state:
        st.session_state.hub_live = AiHub(central_ai=st.session_state.ceo)
    if "hub_sim" not in st.session_state:
        st.session_state.hub_sim = AiHub(central_ai=None)
    if "history" not in st.session_state:
        st.session_state.history = {"cpu_temp": [], "cpu_load": [], "ram_usage": []}
    if "tick" not in st.session_state:
        st.session_state.tick = 0


def record_history(snapshot):
    hist = st.session_state.history
    hist["cpu_temp"].append(snapshot.get("cpu_temp", 0.0))
    hist["cpu_load"].append(snapshot.get("cpu_load", 0.0))
    hist["ram_usage"].append(snapshot.get("ram_usage", 0.0))
    max_points = 60
    for key in hist:
        hist[key] = hist[key][-max_points:]


def render_routing_table(hub, mode_action_payload_builder):
    rows = []
    for mode in MODE_ORDERS:
        task = mode_action_payload_builder()
        result = hub.dispatch(task, mode=mode)
        rows.append({
            "Mode": mode.replace("_", " ").title(),
            "Trace": " → ".join(n.replace("node", "N") for n in result["trace"]),
            "Final Action": FINAL_ACTION_ICON.get(result["final_action"], result["final_action"]),
        })
    st.table(rows)


def main():
    init_state()
    ceo = st.session_state.ceo

    st.title("🧠 SOLO ROCK — Live Control Loop Dashboard")
    st.caption(
        "A visual view of the bio-inspired orchestrator: real telemetry → Central AI decision → "
        "four-node symmetric routing. See the [README](https://github.com/hellomrsys-maker/Solo-Rock-Matrix-Engine-NeuroSys) "
        "for the full architecture."
    )

    # --- Sidebar controls ---
    st.sidebar.header("Controls")
    live_refresh = st.sidebar.checkbox("🔴 Live auto-refresh", value=False)
    refresh_secs = st.sidebar.slider("Refresh interval (s)", 1, 10, 2, disabled=not live_refresh)
    manual_refresh = st.sidebar.button("🔄 Refresh now")

    st.sidebar.divider()
    simulate = st.sidebar.checkbox("🧪 Simulation mode", value=False,
                                    help="Override telemetry with slider values to safely demo "
                                         "THROTTLE / EMERGENCY behavior without a hot CPU.")
    sim_temp = sim_load = sim_ram = None
    if simulate:
        sim_temp = st.sidebar.slider("Simulated CPU temp (°C)", 0, 110, 45)
        sim_load = st.sidebar.slider("Simulated CPU load (%)", 0, 100, 20)
        sim_ram = st.sidebar.slider("Simulated RAM usage (%)", 0, 100, 40)

    with st.sidebar.expander("Decision thresholds"):
        st.write(f"Thermal warning: **{THERMAL_WARNING_C}°C**")
        st.write(f"Thermal critical: **{THERMAL_CRITICAL_C}°C**")
        st.write(f"CPU load — moderate: **{CPU_LOAD_MODERATE_PCT}%**, high: **{CPU_LOAD_HIGH_PCT}%**")
        st.write(f"RAM critical: **{RAM_CRITICAL_PCT}%**")

    # --- Hardware profile ---
    topo = ceo.global_state.topology
    cols = st.columns(5)
    cols[0].metric("OS", topo.os_name)
    cols[1].metric("CPU cores", f"{topo.cpu_physical_cores}p / {topo.cpu_logical_cores}l")
    cols[2].metric("GPUs detected", len(topo.gpus) if topo.gpus else "None")
    cols[3].metric("DPU present", "Yes" if topo.has_dpu else "No")
    cols[4].metric("Routing profile", topo.profile)

    st.divider()

    # --- Telemetry + decision ---
    if simulate:
        # Compute what the Decision Engine *would* decide — never routed through
        # CentralAI.tick(), so simulated numbers can never trigger a real hardware change.
        snapshot = {"cpu_temp": sim_temp, "cpu_load": sim_load, "ram_usage": sim_ram}
        action, reason = ceo.decision_engine.decide(snapshot)
    else:
        # The real control cycle: this is the same call run_control_loop.py makes,
        # and it's what can trigger (and later release) the real Emergency Override.
        action, reason, snapshot = ceo.tick()
        record_history(snapshot)
        st.session_state.tick += 1

    st.subheader("Telemetry")
    t_cols = st.columns(4)
    t_cols[0].metric("CPU temp", f"{snapshot['cpu_temp']:.1f} °C")
    t_cols[1].metric("CPU load", f"{snapshot['cpu_load']:.1f} %")
    t_cols[2].metric("RAM usage", f"{snapshot['ram_usage']:.1f} %")
    battery = snapshot.get("battery_percent")
    t_cols[3].metric("Battery", "N/A" if battery is None else f"{battery:.1f} %")

    st.subheader("Central AI Decision")
    render_action_box(action, reason, simulated=simulate)

    st.subheader("Four-Node Symmetric Routing")
    st.caption(
        "The same task dispatched through all four permutation modes of the ring "
        "(software / executive / balance / hardware-driven) — every mode converges on the same final action."
    )

    if simulate:
        def build_task():
            return {"task_id": "demo-task", "workload_type": "compute", "priority": 1,
                     "executive_policy": action}
        render_routing_table(st.session_state.hub_sim, build_task)
    else:
        # ceo.last_action was already set by ceo.tick() above, so the nodes see this tick's decision.
        def build_task():
            return {"task_id": "demo-task", "workload_type": "compute", "priority": 1}
        render_routing_table(st.session_state.hub_live, build_task)

    # --- History chart (real telemetry only) ---
    if not simulate and len(st.session_state.history["cpu_temp"]) > 1:
        st.subheader(f"Telemetry History (last {len(st.session_state.history['cpu_temp'])} ticks)")
        st.line_chart(st.session_state.history)

    st.divider()
    st.caption(
        "Safety model: this dashboard never raises any limit above the manufacturer default. "
        "Simulation mode never touches real hardware controls — only Live mode's EMERGENCY path can, "
        "and only on Windows with an administrator shell. See the README's Safety Model section."
    )

    if live_refresh and not simulate:
        time.sleep(refresh_secs)
        st.rerun()
    elif manual_refresh:
        st.rerun()


if __name__ == "__main__":
    main()
