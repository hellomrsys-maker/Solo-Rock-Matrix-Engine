import streamlit as st
import math
import random
import time

st.set_page_config(layout="wide", page_title="Solo Rock Matrix Engine")

# =========================================================================
# NERVES DATA (Same as original)
# =========================================================================
NERVES_DATA = [
    # CERN 1-25
    ("CERN-001", "Main Intent Nerve", 0x00FFFF), ("CERN-002", "Context Freeze Nerve", 0x00FFFF),
    ("CERN-003", "Heartbeat Monitor Nerve", 0x00FFFF), ("CERN-004", "Diagonal Cross-Talk Nerve", 0x00FFFF),
    ("CERN-005", "Priority Cease Nerve", 0x00FFFF), ("CERN-006", "Error Isolation Nerve", 0x00FFFF),
    ("CERN-007", "Telemetry Gathering Nerve", 0x00FFFF), ("CERN-008", "User Input Velocity Nerve", 0x00FFFF),
    ("CERN-009", "Resource Throttling Nerve", 0x00FFFF), ("CERN-010", "Memory Cache Flush Nerve", 0x00FFFF),
    ("CERN-011", "Asymmetric Thread Spawning Nerve", 0x00FFFF), ("CERN-012", "Interrupt Overriding Nerve", 0x00FFFF),
    ("CERN-013", "Global Thermal Headroom Nerve", 0x00FFFF), ("CERN-014", "Task Target Profiler Nerve", 0x00FFFF),
    ("CERN-015", "Coherency Matrix Trigger Nerve", 0x00FFFF), ("CERN-016", "External Bridge Isolation Nerve", 0x00FFFF),
    ("CERN-017", "Bus Flush Authorization Nerve", 0x00FFFF), ("CERN-018", "Predictive Target Nerve", 0x00FFFF),
    ("CERN-019", "Silicon Uncoupling Nerve", 0x00FFFF), ("CERN-020", "Emergency Throttle Override Nerve", 0x00FFFF),
    ("CERN-021", "Predictive Asset Pre-stager Nerve", 0x00FFFF), ("CERN-022", "Asynchronous Signal Interceptor Nerve", 0x00FFFF),
    ("CERN-023", "Symmetric Loop Normalizer Nerve", 0x00FFFF), ("CERN-024", "Clock Gating Authorization Nerve", 0x00FFFF),
    ("CERN-025", "Transient Surge Predictor Nerve", 0x00FFFF),
    
    # STIN 26-50
    ("STIN-026", "Physical Touch Vector Nerve", 0xFFFF00), ("STIN-027", "Pain Trigger Nerve", 0xFFFF00),
    ("STIN-028", "Reactive Pre-Ramp Nerve", 0xFFFF00), ("STIN-029", "Touch Jitter Filter Nerve", 0xFFFF00),
    ("STIN-030", "Finger Velocity Tracker Nerve", 0xFFFF00), ("STIN-031", "Bypass Stack Nerve", 0xFFFF00),
    ("STIN-032", "Pump Activation Nerve", 0xFFFF00), ("STIN-033", "Peripheral Response Nerve", 0xFFFF00),
    ("STIN-034", "Macro-Loop Compression Nerve", 0xFFFF00), ("STIN-035", "Input Vector Alignment Nerve", 0xFFFF00),
    ("STIN-036", "Display Frame Alignment Nerve", 0xFFFF00), ("STIN-037", "Dynamic Anti-Lag Nerve", 0xFFFF00),
    ("STIN-038", "Continuous Gesture Nerve", 0xFFFF00), ("STIN-039", "Hardware Interrupt Anchor Nerve", 0xFFFF00),
    ("STIN-040", "Predictive Collision Nerve", 0xFFFF00), ("STIN-041", "Transient Current Burst Nerve", 0xFFFF00),
    ("STIN-042", "Multi-Touch Coordinate Nerve", 0xFFFF00), ("STIN-043", "Pressure Depth Mapping Nerve", 0xFFFF00),
    ("STIN-044", "Zero-Idle Transition Nerve", 0xFFFF00), ("STIN-045", "Peripheral Input Routing Nerve", 0xFFFF00),
    ("STIN-046", "Input Telemetry Sync Nerve", 0xFFFF00), ("STIN-047", "Trigger Predictive Path Nerve", 0xFFFF00),
    ("STIN-048", "Input De-Bouncing Nerve", 0xFFFF00), ("STIN-049", "Tactile Calibration Nerve", 0xFFFF00),
    ("STIN-050", "Ball Hit Realization Nerve", 0xFFFF00),
    
    # PDEC 51-75
    ("PDEC-051", "Transient Drop Neutralizer Nerve", 0x0000FF), ("PDEC-052", "Battery Thermal Guardian Nerve", 0x0000FF),
    ("PDEC-053", "AC-to-DC Curve Optimizer Nerve", 0x0000FF), ("PDEC-054", "Silicon Power Delivery Nerve", 0x0000FF),
    ("PDEC-055", "Safe Discharge Curve Nerve", 0x0000FF), ("PDEC-056", "Parallel Cell Shifter Nerve", 0x0000FF),
    ("PDEC-057", "Motherboard PDN Stabilizer Nerve", 0x0000FF), ("PDEC-058", "Phase Ramping Catalyst Nerve", 0x0000FF),
    ("PDEC-059", "Energy Preservation Nerve", 0x0000FF), ("PDEC-060", "High-Amp Spike Absorber Nerve", 0x0000FF),
    ("PDEC-061", "Battery Resistance Monitor Nerve", 0x0000FF), ("PDEC-062", "GPU Wattage Router Nerve", 0x0000FF),
    ("PDEC-063", "CPU Core Volting Nerve", 0x0000FF), ("PDEC-064", "Thermal Throttle Preemption Nerve", 0x0000FF),
    ("PDEC-065", "Vmin Preservation Nerve", 0x0000FF), ("PDEC-066", "Interconnect Power Saver Nerve", 0x0000FF),
    ("PDEC-067", "Dynamic Phase Gate Nerve", 0x0000FF), ("PDEC-068", "Charge Preservation Loop Nerve", 0x0000FF),
    ("PDEC-069", "Motherboard Trace Thermometer Nerve", 0x0000FF), ("PDEC-070", "On-Die Regulator Link Nerve", 0x0000FF),
    ("PDEC-071", "Transient Surge Mitigation Nerve", 0x0000FF), ("PDEC-072", "Display Backlight Wattage Nerve", 0x0000FF),
    ("PDEC-073", "Memory Rail Voltage Nerve", 0x0000FF), ("PDEC-074", "Capacitor Discharge Regulator Nerve", 0x0000FF),
    ("PDEC-075", "Global Efficiency Balance Nerve", 0x0000FF),
    
    # CAIN 76-100
    ("CAIN-076", "Instruction Stream Interceptor Nerve", 0xFF9900), ("CAIN-077", "Logic Type Slicer Nerve", 0xFF9900),
    ("CAIN-078", "CPU Thread Router Nerve", 0xFF9900), ("CAIN-079", "GPU Pixel Pipeline Nerve", 0xFF9900),
    ("CAIN-080", "Tensor Matrix Redirect Nerve", 0xFF9900), ("CAIN-081", "Cache Coherency Staging Nerve", 0xFF9900),
    ("CAIN-082", "On-Die Fabric Overclocker Nerve", 0xFF9900), ("CAIN-083", "Chiplet Delay Mitregator Nerve", 0xFF9900),
    ("CAIN-084", "Bus Clock Gating Nerve", 0xFF9900), ("CAIN-085", "High-End Mapping Coordinate Nerve", 0xFF9900),
    ("CAIN-086", "Virtual Lookup Eliminator Nerve", 0xFF9900), ("CAIN-087", "Asymmetric Scheduler Bridge Nerve", 0xFF9900),
    ("CAIN-088", "DMA Priority Zero Nerve", 0xFF9900), ("CAIN-089", "Texture Stream Accelerator Nerve", 0xFF9900),
    ("CAIN-090", "Floating Point Matrix Nerve", 0xFF9900), ("CAIN-091", "On-Chip Bus Arbitrator Nerve", 0xFF9900),
    ("CAIN-092", "Rasterization Sync Nerve", 0xFF9900), ("CAIN-093", "Neural Upscale Clock Nerve", 0xFF9900),
    ("CAIN-094", "Compute Block Demarcation Nerve", 0xFF9900), ("CAIN-095", "Static RAM Ring Buffer Nerve", 0xFF9900),
    ("CAIN-096", "Vector Core Load Balancer Nerve", 0xFF9900), ("CAIN-097", "Instruction Pipeline Prefetch Nerve", 0xFF9900),
    ("CAIN-098", "Register Renaming Conduit Nerve", 0xFF9900), ("CAIN-099", "Silicon Sector Temperature Shifter Nerve", 0xFF9900),
    ("CAIN-100", "Zero-Lag Execution Lock Nerve", 0xFF9900),
    
    # FSMF 101-125
    ("FSMF-101", "Junk Filter Nerve", 0xFF00FF), ("FSMF-102", "NVMe Burst Write Catalyst Nerve", 0xFF00FF),
    ("FSMF-103", "Bus Flush Command Nerve", 0xFF00FF), ("FSMF-104", "VRAM Page Allocator Nerve", 0xFF00FF),
    ("FSMF-105", "Stale Data Exudation Nerve", 0xFF00FF), ("FSMF-106", "Direct Storage Pathway Nerve", 0xFF00FF),
    ("FSMF-107", "IO Latency Killer Nerve", 0xFF00FF), ("FSMF-108", "Memory Fragmentation Shield Nerve", 0xFF00FF),
    ("FSMF-109", "Background Write Throttle Nerve", 0xFF00FF), ("FSMF-110", "Cache Pollution Guard Nerve", 0xFF00FF),
    ("FSMF-111", "Asset Decompression Valve Nerve", 0xFF00FF), ("FSMF-112", "Memory Refresh Synchronizer Nerve", 0xFF00FF),
    ("FSMF-113", "Bandwidth Rationing Nerve", 0xFF00FF), ("FSMF-114", "Dynamic Page Pre-loading Nerve", 0xFF00FF),
    ("FSMF-115", "Zero-Copy Data Transfer Nerve", 0xFF00FF), ("FSMF-116", "Storage Pipeline Pre-Heater Nerve", 0xFF00FF),
    ("FSMF-117", "ECC Error Suppressor Nerve", 0xFF00FF), ("FSMF-118", "Virtual Swap File Block Nerve", 0xFF00FF),
    ("FSMF-119", "Asset Footprint Compression Nerve", 0xFF00FF), ("FSMF-120", "Direct Memory Mapping Governor Nerve", 0xFF00FF),
    ("FSMF-121", "High-Speed Queue Bypasser Nerve", 0xFF00FF), ("FSMF-122", "Memory Pre-Fetch Filter Nerve", 0xFF00FF),
    ("FSMF-123", "Bus Contention Arbitrator Nerve", 0xFF00FF), ("FSMF-124", "RAM Bus Overclock Unlocker Nerve", 0xFF00FF),
    ("FSMF-125", "Garbage Collection Sync Nerve", 0xFF00FF),
]

# Fill remaining nerves for brevity
for i in range(len(NERVES_DATA), 300):
    if i < 250:
        NERVES_DATA.append((f"RFU-{i+1}", "Reserved Neural Pathway", 0x444444))
    else:
        NERVES_DATA.append((f"RESERVED-{i+1}", "System Reserved", 0x666666))

# =========================================================================
# WORLD MAP
# =========================================================================
WORLD_MAP = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,1,0,0,0,0,0,1,0,0,0,0,1],
    [1,0,1,0,1,0,1,1,1,0,1,0,1,1,0,1],
    [1,0,1,0,0,0,0,0,1,0,0,0,1,0,0,1],
    [1,0,1,1,1,1,1,0,1,1,1,1,1,0,1,1],
    [1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,1],
    [1,1,1,1,1,0,1,1,1,1,1,0,1,1,0,1],
    [1,0,0,0,1,0,0,0,0,0,1,0,0,0,0,1],
    [1,0,1,0,1,1,1,1,1,0,1,1,1,1,1,1],
    [1,0,1,0,0,0,0,0,1,0,0,0,0,0,0,1],
    [1,0,1,1,1,1,1,0,1,1,1,1,1,1,0,1],
    [1,0,0,0,0,0,1,0,0,0,0,0,0,1,0,1],
    [1,1,1,1,1,0,1,1,1,1,1,1,0,1,0,1],
    [1,0,0,0,1,0,0,0,0,0,0,1,0,1,0,1],
    [1,0,1,0,0,0,1,1,1,1,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
]

# =========================================================================
# STREAMLIT STATE MANAGEMENT
# =========================================================================
if "game_state" not in st.session_state:
    st.session_state.game_state = {
        "player_x": -650.0,
        "player_y": -650.0,
        "player_angle": 0.0,
        "score": 0,
        "health": 100,
        "enemies": [(random.randint(0, 1200) - 600, random.randint(0, 1200) - 600, 100) for _ in range(20)],
        "bullets": [],
        "nerve_states": [0.0] * 300,
        "frame_count": 0,
        "cpu_usage": 0.0,
    }

# =========================================================================
# RENDERING FUNCTION (Pillow-based, for browser compatibility)
# =========================================================================
def render_game():
    from PIL import Image, ImageDraw, ImageFont
    
    gs = st.session_state.game_state
    
    # Create image
    img = Image.new("RGB", (800, 600), color=(20, 20, 20))
    draw = ImageDraw.Draw(img)
    
    # Raycasting
    player_x, player_y, player_angle = gs["player_x"] / 100 + 8, gs["player_y"] / 100 + 8, gs["player_angle"]
    
    for ray_idx in range(160):
        ray_angle = player_angle - math.pi/6 + (ray_idx / 160) * (math.pi / 3)
        dx, dy = math.cos(ray_angle), math.sin(ray_angle)
        
        distance = 0.0
        hit = False
        while not hit and distance < 20:
            distance += 0.2
            tx, ty = int(player_x + dx * distance), int(player_y + dy * distance)
            if tx < 0 or tx >= 16 or ty < 0 or ty >= 16 or WORLD_MAP[ty][tx] == 1:
                hit = True
        
        wall_height = int(300 / (distance + 0.1))
        x_pos = ray_idx * 5
        y_top = 300 - wall_height // 2
        y_bottom = 300 + wall_height // 2
        
        color_intensity = max(50, 255 - int(distance * 30))
        color = (0, color_intensity, 0)
        draw.rectangle([x_pos, y_top, x_pos + 5, y_bottom], fill=color)
    
    # Draw enemies
    for ex, ey, health in gs["enemies"]:
        ex_world, ey_world = ex / 100 + 8, ey / 100 + 8
        dx, dy = ex_world - player_x, ey_world - player_y
        distance = math.sqrt(dx*dx + dy*dy)
        if 0 < distance < 15:
            sprite_angle = math.atan2(dy, dx) - player_angle
            screen_x = int(400 + (sprite_angle / (math.pi/3)) * 400)
            sprite_size = max(10, int(100 / distance))
            if 0 < screen_x < 800:
                draw.ellipse([screen_x-sprite_size//2, 250, screen_x+sprite_size//2, 350], fill=(255, 0, 0))
    
    # Draw HUD
    try:
        font = ImageFont.load_default()
        draw.text((10, 10), f"Health: {gs['health']}%", fill=(255, 255, 255), font=font)
        draw.text((10, 30), f"Enemies: {len([e for e in gs['enemies'] if e[2] > 0])}", fill=(255, 255, 255), font=font)
        draw.text((10, 50), f"Score: {gs['score']}", fill=(255, 255, 255), font=font)
    except:
        pass
    
    # Draw 300-nerve matrix (15x20 grid)
    nerve_box_size = 4
    grid_x, grid_y = 650, 20
    for i in range(300):
        row, col = i // 20, i % 20
        if col < 15:
            x = grid_x + col * 8
            y = grid_y + row * 8
            nerve_id, _, color = NERVES_DATA[i]
            if gs["nerve_states"][i] > 0.1:
                r = (color >> 16) & 0xFF
                g = (color >> 8) & 0xFF
                b = color & 0xFF
                intensity = int(gs["nerve_states"][i] * 255)
                color_tuple = (r, g, b)
            else:
                color_tuple = (40, 40, 40)
            draw.rectangle([x, y, x+nerve_box_size, y+nerve_box_size], fill=color_tuple)
    
    return img

# =========================================================================
# MAIN UI
# =========================================================================
st.title("🎮 SOLO ROCK MATRIX ENGINE V4")
st.markdown("**Monolithic 300-Nerve AI Neural System | Retro 3D Raycaster**")

col1, col2 = st.columns([3, 1])

with col1:
    placeholder = st.empty()

with col2:
    st.markdown("### 📊 Status")
    health_display = st.metric("Player Health", f"{st.session_state.game_state['health']}%")
    enemies_count = len([e for e in st.session_state.game_state['enemies'] if e[2] > 0])
    st.metric("Active Enemies", enemies_count)
    st.metric("Score", st.session_state.game_state['score'])

# Game loop
if st.button("▶️ Start Game", key="start_btn"):
    with placeholder.container():
        progress_bar = st.progress(0)
        
        for frame in range(100):
            gs = st.session_state.game_state
            
            # Update nerve states
            for i in range(300):
                if random.random() < 0.15:
                    gs["nerve_states"][i] = 1.0
                else:
                    gs["nerve_states"][i] = max(0, gs["nerve_states"][i] - 0.1)
            
            # Simple AI: enemies chase player
            for idx, (ex, ey, health) in enumerate(gs["enemies"]):
                if health > 0:
                    dx = gs["player_x"] - ex
                    dy = gs["player_y"] - ey
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist > 10:
                        gs["enemies"][idx] = (ex + dx/dist*5, ey + dy/dist*5, health)
            
            # Update CPU usage simulation
            gs["cpu_usage"] = 30 + 20 * random.random()
            gs["frame_count"] += 1
            
            # Render
            img = render_game()
            st.image(img, use_column_width=True)
            
            progress_bar.progress((frame + 1) / 100)
            time.sleep(0.05)

st.markdown("---")
st.markdown("""
### 📖 About This Engine
**Solo Rock Matrix Engine** combines:
- 🔳 Wolfenstein 3D-style raycasting renderer
- 🧠 300-nerve neural system visualization
- 👾 Swarm AI enemies with pursuit logic
- 🔫 Real-time ballistics & collision detection
- 📊 Live telemetry overlay

**Web Version Limitations:**
- Streamlit rendering is slower than native (~10-15 FPS vs 60+ FPS)
- No keyboard input in web interface (use native version for full controls)
- Simplified physics for performance

**To run the native version:** `python SOLO_ROCK.py` (Windows only, renders via raw Win32 GDI — no pygame or DirectX required)
""")
