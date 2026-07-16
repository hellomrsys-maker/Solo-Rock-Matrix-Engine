#!/usr/bin/env python3
"""
SOLO ROCK Analytics Dashboard — Streamlit app for historical telemetry analysis and trend detection.

Shows:
- Last 1h/1d/1w temperature, load, RAM trends with statistics
- Decision distribution over time
- Thermal trend detection (rising/falling)
- Performance metrics and throttle impact calculation
- Alert frequency and patterns
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from diagnostics.logger import EventLogger
from analytics.query import TelemetryAnalyzer

# Page config
st.set_page_config(
    page_title="SOLO ROCK Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main { padding: 2rem; }
    .stMetric { text-align: center; }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'logger' not in st.session_state:
    st.session_state.logger = EventLogger()
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = TelemetryAnalyzer()

logger = st.session_state.logger
analyzer = st.session_state.analyzer

# Title
st.title("📊 SOLO ROCK Analytics Dashboard")
st.markdown("Historical telemetry analysis, trend detection, and performance metrics")

# Sidebar: Time range selection
st.sidebar.header("Analysis Settings")
time_range = st.sidebar.selectbox(
    "Time Range",
    options=["Last 1 Hour", "Last 24 Hours", "Last 7 Days"],
    index=0
)

# Map selection to hours
time_hours = {
    "Last 1 Hour": 1,
    "Last 24 Hours": 24,
    "Last 7 Days": 168
}[time_range]

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

# Auto-refresh interval
auto_refresh = st.sidebar.checkbox("Auto-refresh every 30s", value=False)
if auto_refresh:
    st.markdown("""
    <script>
    setTimeout(function() {
        window.parent.document.querySelector('[data-testid="stDecoration"]').click();
    }, 30000);
    </script>
    """, unsafe_allow_html=True)

# Get data
try:
    since_timestamp = (datetime.now() - timedelta(hours=time_hours)).timestamp()
    events = logger.get_events_since(since_timestamp)

    if not events:
        st.warning(f"⚠️ No data available for {time_range}. Run `python monitor_realtime.py` to collect telemetry.")
        st.stop()

    # Convert to DataFrame
    df = pd.DataFrame(events)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

    # Key Metrics
    st.header("Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        avg_temp = df['cpu_temp'].mean() if 'cpu_temp' in df.columns else 0
        st.metric("Avg Temperature", f"{avg_temp:.1f}°C",
                 delta=f"{df['cpu_temp'].iloc[-1] - df['cpu_temp'].iloc[0]:.1f}°C" if len(df) > 0 else "0°C")

    with col2:
        max_temp = df['cpu_temp'].max() if 'cpu_temp' in df.columns else 0
        st.metric("Max Temperature", f"{max_temp:.1f}°C")

    with col3:
        avg_load = df['cpu_load'].mean() if 'cpu_load' in df.columns else 0
        st.metric("Avg CPU Load", f"{avg_load:.1f}%")

    with col4:
        avg_ram = df['ram_usage'].mean() if 'ram_usage' in df.columns else 0
        st.metric("Avg RAM Usage", f"{avg_ram:.1f}%")

    with col5:
        total_events = len(df)
        st.metric("Total Events", f"{total_events}")

    # Thermal Analysis
    st.header("🌡️ Thermal Analysis")
    col1, col2 = st.columns(2)

    with col1:
        # Temperature trend
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['cpu_temp'],
            mode='lines',
            name='CPU Temperature',
            line=dict(color='#FF6B6B', width=2),
            fill='tozeroy',
            fillcolor='rgba(255, 107, 107, 0.2)'
        ))

        # Add warning/critical thresholds
        fig_temp.add_hline(y=80, line_dash="dash", line_color="orange",
                          annotation_text="Warning (80°C)", annotation_position="right")
        fig_temp.add_hline(y=90, line_dash="dash", line_color="red",
                          annotation_text="Critical (90°C)", annotation_position="right")

        fig_temp.update_layout(
            title="CPU Temperature Trend",
            xaxis_title="Time",
            yaxis_title="Temperature (°C)",
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig_temp, use_container_width=True)

    with col2:
        # Temperature statistics
        stats = analyzer.get_thermal_statistics(hours=time_hours)
        if stats:
            temp_data = stats.get('temp', {})
            st.metric("Average", f"{temp_data.get('avg', 0):.1f}°C")
            st.metric("Minimum", f"{temp_data.get('min', 0):.1f}°C")
            st.metric("Maximum", f"{temp_data.get('max', 0):.1f}°C")

            # Thermal trend
            trend = analyzer.detect_thermal_trend(minutes=30)
            if trend:
                trend_text = "📈 Rising" if trend else "📉 Falling"
                st.metric("30-min Trend", trend_text)

            # Throttle impact
            throttle_impact = analyzer.get_throttle_impact(hours=time_hours)
            if throttle_impact:
                st.metric("Time Throttled", f"{throttle_impact.get('throttle_percent', 0):.1f}%")

    # CPU Load Analysis
    st.header("⚙️ CPU Load Analysis")
    col1, col2 = st.columns(2)

    with col1:
        fig_load = go.Figure()
        fig_load.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['cpu_load'],
            mode='lines',
            name='CPU Load',
            line=dict(color='#4ECDC4', width=2),
            fill='tozeroy',
            fillcolor='rgba(78, 205, 196, 0.2)'
        ))

        fig_load.add_hline(y=85, line_dash="dash", line_color="orange",
                          annotation_text="High (85%)", annotation_position="right")
        fig_load.add_hline(y=95, line_dash="dash", line_color="red",
                          annotation_text="Critical (95%)", annotation_position="right")

        fig_load.update_layout(
            title="CPU Load Trend",
            xaxis_title="Time",
            yaxis_title="Load (%)",
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig_load, use_container_width=True)

    with col2:
        load_trend = analyzer.get_load_trend(minutes=30)
        if load_trend:
            load_data = load_trend.get('load', {})
            st.metric("Average Load", f"{load_data.get('avg', 0):.1f}%")
            st.metric("Peak Load", f"{load_data.get('max', 0):.1f}%")
            st.metric("Min Load", f"{load_data.get('min', 0):.1f}%")

            trend_direction = "📈 Rising" if load_trend.get('is_rising', False) else "📉 Falling"
            st.metric("30-min Load Trend", trend_direction)

    # RAM Analysis
    st.header("💾 RAM Usage Analysis")
    fig_ram = go.Figure()
    fig_ram.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['ram_usage'],
        mode='lines',
        name='RAM Usage',
        line=dict(color='#95E1D3', width=2),
        fill='tozeroy',
        fillcolor='rgba(149, 225, 211, 0.2)'
    ))

    fig_ram.add_hline(y=97, line_dash="dash", line_color="red",
                     annotation_text="Critical (97%)", annotation_position="right")

    fig_ram.update_layout(
        title="RAM Usage Trend",
        xaxis_title="Time",
        yaxis_title="Usage (%)",
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig_ram, use_container_width=True)

    # Decision Distribution
    st.header("🎯 Decision Distribution")
    col1, col2 = st.columns(2)

    with col1:
        dist = analyzer.get_decision_distribution(hours=time_hours)
        if dist:
            decision_counts = dist.get('counts', {})
            decision_pcts = dist.get('percentages', {})

            # Pie chart
            fig_pie = px.pie(
                values=list(decision_counts.values()),
                names=list(decision_counts.keys()),
                title="Decisions by Frequency",
                color_discrete_map={
                    'FULL_RATE': '#2ECC71',
                    'BATCH': '#3498DB',
                    'THROTTLE': '#F39C12',
                    'EMERGENCY': '#E74C3C'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Decision breakdown table
        if dist:
            decision_data = []
            for decision, count in decision_counts.items():
                pct = decision_pcts.get(decision, 0)
                decision_data.append({
                    'Decision': decision,
                    'Count': count,
                    'Percentage': f"{pct:.1f}%"
                })

            df_decisions = pd.DataFrame(decision_data)
            st.dataframe(df_decisions, use_container_width=True)

            # Orchestration impact
            pacing_decisions = (decision_counts.get('BATCH', 0) +
                              decision_counts.get('THROTTLE', 0) +
                              decision_counts.get('EMERGENCY', 0))
            total = sum(decision_counts.values())
            pacing_pct = (pacing_decisions / total * 100) if total > 0 else 0

            st.metric("Orchestration Impact", f"{pacing_pct:.1f}% paced/throttled")

    # Detailed Performance Metrics
    st.header("📈 Performance Metrics")
    metrics = analyzer.get_performance_metrics(hours=time_hours)

    if metrics:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("Temperature")
            temp = metrics.get('temperatures', {})
            st.write(f"**Average:** {temp.get('avg', 0):.1f}°C")
            st.write(f"**Min:** {temp.get('min', 0):.1f}°C")
            st.write(f"**Max:** {temp.get('max', 0):.1f}°C")

        with col2:
            st.subheader("CPU Load")
            load = metrics.get('cpu_loads', {})
            st.write(f"**Average:** {load.get('avg', 0):.1f}%")
            st.write(f"**Min:** {load.get('min', 0):.1f}%")
            st.write(f"**Max:** {load.get('max', 0):.1f}%")

        with col3:
            st.subheader("RAM Usage")
            ram = metrics.get('ram_usage', {})
            st.write(f"**Average:** {ram.get('avg', 0):.1f}%")
            st.write(f"**Min:** {ram.get('min', 0):.1f}%")
            st.write(f"**Max:** {ram.get('max', 0):.1f}%")

    # Raw Data
    if st.checkbox("📋 Show Raw Data"):
        st.subheader("Event Log")
        # Select columns to display
        display_cols = ['timestamp', 'cpu_temp', 'cpu_load', 'ram_usage', 'decision', 'reason']
        available_cols = [col for col in display_cols if col in df.columns]

        st.dataframe(df[available_cols].tail(100), use_container_width=True)

    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption(f"📊 Data Points: {len(df)}")

    with col2:
        st.caption(f"⏱️ Time Range: {time_range}")

    with col3:
        st.caption(f"🔄 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

except Exception as e:
    st.error(f"❌ Error loading analytics: {e}")
    st.exception(e)
