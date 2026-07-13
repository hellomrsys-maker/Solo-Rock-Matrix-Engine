import sys
import os
import platform

# On non-Windows platforms, SOLO_ROCK.py uses ctypes.windll which doesn't exist.
# Redirect to dashboard.py (cross-platform Streamlit app) instead.
if platform.system() != "Windows":
    import subprocess
    # Execute dashboard.py as a Streamlit app
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run",
         os.path.join(os.path.dirname(__file__), "dashboard.py")],
        cwd=os.path.dirname(__file__)
    )
    sys.exit(0)

import ctypes
import math
import threading
import time
import random
from multiprocessing import shared_memory

# -------------------------------------------------------------------------
# 1. ZERO-BRIDGE SYNCHRONOUS MEMORY ARCHITECTURE (AMSV)
# -------------------------------------------------------------------------
class EntityState(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("x", ctypes.c_float), ("y", ctypes.c_float), ("z", ctypes.c_float),
        ("rx", ctypes.c_float), ("ry", ctypes.c_float), ("rz", ctypes.c_float),
        ("vx", ctypes.c_float), ("vy", ctypes.c_float), ("vz", ctypes.c_float),
        ("health", ctypes.c_float), ("state", ctypes.c_uint32)
    ]

class AtomicMemoryStateVector(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("coord_x", ctypes.c_float), ("coord_y", ctypes.c_float), ("coord_z", ctypes.c_float), ("rotation", ctypes.c_float),
        ("cpu_temp", ctypes.c_float), ("gpu_load", ctypes.c_float), ("ram_usage", ctypes.c_float), ("wattage", ctypes.c_float),
        ("mouse_state", ctypes.c_uint32), ("keyboard_state", ctypes.c_uint32), ("controller_1", ctypes.c_uint32), ("controller_2", ctypes.c_uint32),
        ("ai_target_x", ctypes.c_float), ("ai_target_y", ctypes.c_float), ("health_state", ctypes.c_float), ("time_delta", ctypes.c_float),
        ("entity_count", ctypes.c_uint32), ("entities", EntityState * 256)
    ]

_shm = None
def get_amsv_block():
    global _shm
    mem_name = "SOLO_ROCK_MASTER"
    size = ctypes.sizeof(AtomicMemoryStateVector)
    try:
        _shm = shared_memory.SharedMemory(name=mem_name)
    except FileNotFoundError:
        _shm = shared_memory.SharedMemory(name=mem_name, create=True, size=size)
        _shm.buf[:size] = bytearray(size)
    return AtomicMemoryStateVector.from_buffer(_shm.buf)

amsv_block = get_amsv_block()

# -------------------------------------------------------------------------
# 2. THE 300-NERVE DATABASE & ACTIVATION STATE
# -------------------------------------------------------------------------
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

    # TSN 126-150
    ("TSN-126", "Chassis Telemetry Ingestion Nerve", 0x00FF00), ("TSN-127", "Acoustic Noise Filter Nerve", 0x00FF00),
    ("TSN-128", "Peripheral Polling Booster Nerve", 0x00FF00), ("TSN-129", "Gyro & IMU Ingestion Nerve", 0x00FF00),
    ("TSN-130", "Fan Speed Override Nerve", 0x00FF00), ("TSN-131", "Voltage Sag Warning Nerve", 0x00FF00),
    ("TSN-132", "Ambient Light Sensor Link Nerve", 0x00FF00), ("TSN-133", "Die Temperature Array Nerve", 0x00FF00),
    ("TSN-134", "Haptic Feedback Sync Nerve", 0x00FF00), ("TSN-135", "External Network Ping Nerve", 0x00FF00),
    ("TSN-136", "Packet Drop Mitigator Nerve", 0x00FF00), ("TSN-137", "Peripheral Power Watchdog Nerve", 0x00FF00),
    ("TSN-138", "Transient Noise Suppressor Nerve", 0x00FF00), ("TSN-139", "Core Load Telemetry Nerve", 0x00FF00),
    ("TSN-140", "Bus Utilization Tracker Nerve", 0x00FF00), ("TSN-141", "Display Panel Status Nerve", 0x00FF00),
    ("TSN-142", "Audio Output Latency Nerve", 0x00FF00), ("TSN-143", "Clock Glitch Detector Nerve", 0x00FF00),
    ("TSN-144", "Wireless Interference Filter Nerve", 0x00FF00), ("TSN-145", "Motherboard Flex Thermometer Nerve", 0x00FF00),
    ("TSN-146", "Predictive Thermal Model Nerve", 0x00FF00), ("TSN-147", "Power Rail Monitor Nerve", 0x00FF00),
    ("TSN-148", "External Sensor Interface Nerve", 0x00FF00), ("TSN-149", "Dynamic Noise Floor Adjuster Nerve", 0x00FF00),
    ("TSN-150", "Telemetry Loop Closure Nerve", 0x00FF00),

    # PPVO 151-175
    ("PPVO-151", "Velocity Vector Tracker Nerve", 0xCCFF00), ("PPVO-152", "Collision Pre-Calculator Nerve", 0xCCFF00),
    ("PPVO-153", "Variable Refresh Rate Sync Nerve", 0xCCFF00), ("PPVO-154", "DSC Frame Compressor Nerve", 0xCCFF00),
    ("PPVO-155", "Frame-Gen Handoff Nerve", 0xCCFF00), ("PPVO-156", "Player Path Predictor Nerve", 0xCCFF00),
    ("PPVO-157", "Display Pacing Alignment Nerve", 0xCCFF00), ("PPVO-158", "Post-Processing Valve Nerve", 0xCCFF00),
    ("PPVO-159", "Ray-Tracing Denoise Catalyst Nerve", 0xCCFF00), ("PPVO-160", "Coordinate Matrix Sync Nerve", 0xCCFF00),
    ("PPVO-161", "Audio Spatialization Nerve", 0xCCFF00), ("PPVO-162", "Object Culling Director Nerve", 0xCCFF00),
    ("PPVO-163", "Dynamic Resolution Scaler Nerve", 0xCCFF00), ("PPVO-164", "Vertex Buffer Streamer Nerve", 0xCCFF00),
    ("PPVO-165", "UI Overlay Blending Nerve", 0xCCFF00), ("PPVO-166", "Texture Filtering Accelerator Nerve", 0xCCFF00),
    ("PPVO-167", "Shading Rate Governor Nerve", 0xCCFF00), ("PPVO-168", "Frame Buffer Lock Nerve", 0xCCFF00),
    ("PPVO-169", "Specular Refraction Pre-stage Nerve", 0xCCFF00), ("PPVO-170", "Geometric Detail Level Nerve", 0xCCFF00),
    ("PPVO-171", "Animation Thread Parallelizer Nerve", 0xCCFF00), ("PPVO-172", "Shadow Map Shadow Tracker Nerve", 0xCCFF00),
    ("PPVO-173", "Display Backlight Zone Sync Nerve", 0xCCFF00), ("PPVO-174", "Physics State Serialization Nerve", 0xCCFF00),
    ("PPVO-175", "Visual Output Loop Closer Nerve", 0xCCFF00),

    # SCCN 176-200
    ("SCCN-176", "Pink Loop Main Entry Nerve", 0xFF00FF), ("SCCN-177", "Light Blue Loop Main Entry Nerve", 0xFF00FF),
    ("SCCN-178", "Teal Core Loop Carrier Nerve", 0xFF00FF), ("SCCN-179", "Magenta Core Loop Carrier Nerve", 0xFF00FF),
    ("SCCN-180", "Salmon Core Loop Carrier Nerve", 0xFF00FF), ("SCCN-181", "Orange Core Loop Carrier Nerve", 0xFF00FF),
    ("SCCN-182", "Symmetric Permutation Sync Nerve", 0xFF00FF), ("SCCN-183", "Outer Roof Ring Bridge Nerve", 0xFF00FF),
    ("SCCN-184", "Outer Floor Ring Bridge Nerve", 0xFF00FF), ("SCCN-185", "Left Flank Recirculation Nerve", 0xFF00FF),
    ("SCCN-186", "Right Flank Balance Recirculator Nerve", 0xFF00FF), ("SCCN-187", "Triple Ring Protection Lock Nerve", 0xFF00FF),
    ("SCCN-188", "Shared Coherency Update Nerve", 0xFF00FF), ("SCCN-189", "Zero-Lag Verification Nerve", 0xFF00FF),
    ("SCCN-190", "Asymmetric Balance Matrix Nerve", 0xFF00FF), ("SCCN-191", "Electrical Bus Valve Regulator Nerve", 0xFF00FF),
    ("SCCN-192", "Suspended Stack Interceptor Nerve", 0xFF00FF), ("SCCN-193", "Omnidirectional Core Trigger Nerve", 0xFF00FF),
    ("SCCN-194", "Symmetric State Resolver Nerve", 0xFF00FF), ("SCCN-195", "Chassis Heat Redirection Nerve", 0xFF00FF),
    ("SCCN-196", "Direct Input Vector Injector Nerve", 0xFF00FF), ("SCCN-197", "Dynamic Resolution Trigger Nerve", 0xFF00FF),
    ("SCCN-198", "Cache Allocation Lock Nerve", 0xFF00FF), ("SCCN-199", "Hardware Failure Prevention Nerve", 0xFF00FF),
    ("SCCN-200", "Total Loop Closure Nerve", 0xFF00FF),
]

# Fill Gap 201-250
for i in range(201, 251):
    NERVES_DATA.append((f"RFU-{i}", "Reserved Neural Pathway", 0x444444))

# Append Nerves 251-300
NERVES_DATA.extend([
    # HASW 251-255
    ("HASW-251", "Positional Audio Vector Nerve", 0x0088FF), ("HASW-252", "Acoustic Ray-Tracing Nerve", 0x0088FF),
    ("HASW-253", "Low-Frequency Impact Pump Nerve", 0x0088FF), ("HASW-254", "Spatial Audio Noise Gate Nerve", 0x0088FF),
    ("HASW-255", "Dynamic Voice Mix Isolation Nerve", 0x0088FF),

    # NPW 256-260
    ("NPW-256", "Server Ping Stabilization Nerve", 0x00FF88), ("NPW-257", "Predictive Packet Buffer Nerve", 0x00FF88),
    ("NPW-258", "Wi-Fi/Ethernet Hardware Toggle Nerve", 0x00FF88), ("NPW-259", "Data Frame Error Re-shifter Nerve", 0x00FF88),
    ("NPW-260", "Game Server Direct-Route Nerve", 0x00FF88),

    # RMVG 261-265
    ("RMVG-261", "VRAM Page Lockout Nerve", 0xFF5500), ("RMVG-262", "Texture Tile Decompression Nerve", 0xFF5500),
    ("RMVG-263", "On-Die Memory Bandwidth Booster Nerve", 0xFF5500), ("RMVG-264", "Stale Cache Evacuation Nerve", 0xFF5500),
    ("RMVG-265", "Asymmetric Video Memory Balance Nerve", 0xFF5500),

    # VRFP 266-270
    ("VRFP-266", "Scanline Synchronization Nerve", 0xFF0055), ("VRFP-267", "Synthetic Frame Injection Nerve", 0xFF0055),
    ("VRFP-268", "Display Stream Compression Valve Nerve", 0xFF0055), ("VRFP-269", "Anti-Stutter Pacing Nerve", 0xFF0055),
    ("VRFP-270", "Display Local Dimming Sync Nerve", 0xFF0055),

    # ACOC 271-275
    ("ACOC-271", "Silicon Voltage Spike Cushion Nerve", 0xAA00FF), ("ACOC-272", "Dynamic Thread Spreader Nerve", 0xAA00FF),
    ("ACOC-273", "Micro-Volt Stepping Governor Nerve", 0xAA00FF), ("ACOC-274", "Parasitic Heat Killer Nerve", 0xAA00FF),
    ("ACOC-275", "Frequency Uncoupling Catalyst Nerve", 0xAA00FF),

    # PIDV 276-280
    ("PIDV-276", "Input Jitter Suppression Nerve", 0x55FF00), ("PIDV-277", "High-Polling Frequency Nerve", 0x55FF00),
    ("PIDV-278", "Gesture Trajectory Predictor Nerve", 0x55FF00), ("PIDV-279", "Zero-Delay Controller Pipeline Nerve", 0x55FF00),
    ("PIDV-280", "Tactile Response Calibration Nerve", 0x55FF00),

    # GCLA 281-285
    ("GCLA-281", "View Frustum Object Culling Nerve", 0x00AAFF), ("GCLA-282", "Ray-Tracing Bounce Predictor Nerve", 0x00AAFF),
    ("GCLA-283", "Variable-Rate Shading Director Nerve", 0x00AAFF), ("GCLA-284", "Vertex Buffer Stream Catalyst Nerve", 0x00AAFF),
    ("GCLA-285", "Shadow Map Shadow Tracker Nerve", 0x00AAFF),

    # ILCS 286-300
    ("ILCS-286", "Pink Loop Reverse Carrier Nerve", 0xFFFFFF), ("ILCS-287", "Light Blue Loop Reverse Carrier Nerve", 0xFFFFFF),
    ("ILCS-288", "Diagonal Cross-Track Telemetry Nerve", 0xFFFFFF), ("ILCS-289", "Shared Memory Coherency Validator Nerve", 0xFFFFFF),
    ("ILCS-290", "Triple Isolation Shield Key Nerve", 0xFFFFFF), ("ILCS-291", "Electrical Trace Width Alternator Nerve", 0xFFFFFF),
    ("ILCS-292", "Suspended Task Stack Guard Nerve", 0xFFFFFF), ("ILCS-293", "Omnidirectional Impulse Trigger Nerve", 0xFFFFFF),
    ("ILCS-294", "Symmetric State Resolver Nerve", 0xFFFFFF), ("ILCS-295", "Silicon Block Temperature Shifter Nerve", 0xFFFFFF),
    ("ILCS-296", "Direct Input Matrix Injector Nerve", 0xFFFFFF), ("ILCS-297", "Dynamic Scale Engine Trigger Nerve", 0xFFFFFF),
    ("ILCS-298", "Cache Allocation Priority Lock Nerve", 0xFFFFFF), ("ILCS-299", "Hardware Crash Protection Shield Nerve", 0xFFFFFF),
    ("ILCS-300", "Total System Convergence Nerve", 0xFFFFFF),
])

# Initialize states for 300 nerves
nerve_states = [0.0] * 300

def update_ansm_telemetry():
    while True:
        # Simulate neural action potentials firing down the channels
        for i in range(300):
            if random.random() < 0.15:
                nerve_states[i] = 1.0 # Fire!
            else:
                nerve_states[i] = max(0.0, nerve_states[i] - 0.1) # Decay
        time.sleep(0.05)

# -------------------------------------------------------------------------
# 3. WORLD DATA
# -------------------------------------------------------------------------
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

# -------------------------------------------------------------------------
# 4. AI HARDWARE CONTROLLER (THE OVERLORD)
# -------------------------------------------------------------------------
def get_cpu_times():
    class FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", ctypes.c_uint), ("dwHighDateTime", ctypes.c_uint)]
    idle, kernel, user = FILETIME(), FILETIME(), FILETIME()
    ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user))
    def ft_to_int(ft): return (ft.dwHighDateTime << 32) | ft.dwLowDateTime
    return ft_to_int(idle), ft_to_int(kernel), ft_to_int(user)

def ai_hardware_overlord():
    last_idle, last_kernel, last_user = get_cpu_times()
    while True:
        time.sleep(1.0)
        idle, kernel, user = get_cpu_times()
        sys_diff = (kernel + user) - (last_kernel + last_user)
        idle_diff = idle - last_idle
        
        cpu_usage = ((sys_diff - idle_diff) / sys_diff) * 100.0 if sys_diff > 0 else 0.0
        amsv_block.cpu_temp = cpu_usage 
        
        if cpu_usage > 50.0:
            amsv_block.gpu_load = max(0.2, amsv_block.gpu_load - 0.2)
        else:
            amsv_block.gpu_load = min(1.0, amsv_block.gpu_load + 0.1)
            
        last_idle, last_kernel, last_user = idle, kernel, user

# -------------------------------------------------------------------------
# 5. SENSORY INPUT & AUDIO
# -------------------------------------------------------------------------
def input_nerve():
    user32 = ctypes.windll.user32
    while True:
        state = 0
        if (user32.GetAsyncKeyState(0x57) & 0x8000) != 0: state |= (1 << 0) # W
        if (user32.GetAsyncKeyState(0x41) & 0x8000) != 0: state |= (1 << 1) # A
        if (user32.GetAsyncKeyState(0x53) & 0x8000) != 0: state |= (1 << 2) # S
        if (user32.GetAsyncKeyState(0x44) & 0x8000) != 0: state |= (1 << 3) # D
        if (user32.GetAsyncKeyState(0x20) & 0x8000) != 0: state |= (1 << 4) # Space (Fire)
        if (user32.GetAsyncKeyState(0x0D) & 0x8000) != 0: state |= (1 << 7) # Enter
        amsv_block.keyboard_state = state
        time.sleep(0.016)

def audio_nerve():
    while True:
        if amsv_block.state == 0 and amsv_block.entities[0].health <= 0:
            ctypes.windll.kernel32.Beep(400, 500) # Death sound
        if (amsv_block.keyboard_state & (1 << 4)) != 0: # Fire sound
            ctypes.windll.kernel32.Beep(1200, 50)
        time.sleep(0.1)

# -------------------------------------------------------------------------
# 6. SOFTWARE ENGINE: RENDERER (PPVO)
# -------------------------------------------------------------------------
def render_nerve():
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

    hbrush_floor = gdi32.CreateSolidBrush(0x00221111)
    hbrush_ceil = gdi32.CreateSolidBrush(0x00050505)
    hbrush_wall = gdi32.CreateSolidBrush(0x0000FF00) # Green Walls
    hbrush_red = gdi32.CreateSolidBrush(0x000000FF) # Enemies
    hbrush_yellow = gdi32.CreateSolidBrush(0x0000FFFF) # Bullets
    hbrush_black = gdi32.CreateSolidBrush(0x00000000)
    
    screen_w, screen_h = 800, 600
    
    while True:
        try:
            hdc = user32.GetDC(0)
            if hdc:
                if amsv_block.state == 5:
                    rc_full = RECT(0, 0, screen_w, screen_h)
                    user32.FillRect(hdc, ctypes.byref(rc_full), gdi32.CreateSolidBrush(0x000000))
                    gdi32.SetTextColor(hdc, 0x00FF00)
                    gdi32.SetBkColor(hdc, 0x000000)
                    gdi32.SetBkMode(hdc, 2)
                    title = "=====================================================\n"
                    title += "        SOLO ROCK V4: MONOLITHIC AI EDITION\n"
                    title += "=====================================================\n\n"
                    title += "ALL 300 NERVE CHANNELS CONNECTED & LOGGED IN REAL-TIME.\n"
                    title += "Zero-Bridge Memory Architecture online.\n"
                    title += "Avoid the Swarm. Escape the Matrix.\n\n"
                    title += "PRESS ENTER TO RUN DIAGNOSTICS & SYSTEM MATRIX...\n"
                    user32.DrawTextW(hdc, title, -1, ctypes.byref(rc_full), 0x0000)
                    user32.ReleaseDC(0, hdc)
                    time.sleep(0.016)
                    continue

                me = amsv_block.entities[0]
                px, py, pa = me.x / 100.0 + 8.0, me.y / 100.0 + 8.0, me.ry
                
                # Clear Screen
                user32.FillRect(hdc, ctypes.byref(RECT(0, 0, screen_w, screen_h // 2)), hbrush_ceil)
                user32.FillRect(hdc, ctypes.byref(RECT(0, screen_h // 2, screen_w, screen_h)), hbrush_floor)
                
                throttle = max(0.2, min(1.0, amsv_block.gpu_load))
                num_rays = int(160 * throttle) 
                strip_width = screen_w // num_rays
                
                fov = math.pi / 3.0
                z_buffer = [0] * num_rays
                
                for r in range(num_rays):
                    ray_angle = (pa - fov / 2.0) + (float(r) / float(num_rays)) * fov
                    eye_x, eye_y = math.cos(ray_angle), math.sin(ray_angle)
                    
                    dist, hit = 0.0, False
                    while not hit and dist < 20.0:
                        dist += 0.2
                        tx, ty = int(px + eye_x * dist), int(py + eye_y * dist)
                        if tx < 0 or tx >= 16 or ty < 0 or ty >= 16:
                            hit = True; dist = 20.0
                        elif WORLD_MAP[ty][tx] == 1:
                            hit = True
                    
                    z_buffer[r] = dist
                    ceiling = float(screen_h / 2.0) - screen_h / float(dist)
                    floor = screen_h - ceiling
                    
                    rc_wall = RECT(r * strip_width, int(ceiling), (r + 1) * strip_width, int(floor))
                    user32.FillRect(hdc, ctypes.byref(rc_wall), hbrush_wall)
                
                # Draw Sprites (Swarm and Bullets)
                for i in range(1, 100):
                    e = amsv_block.entities[i]
                    if e.z > 0 or e.health > 0:
                        ex, ey = e.x / 100.0 + 8.0, e.y / 100.0 + 8.0
                        dx, dy = ex - px, ey - py
                        dist = math.sqrt(dx*dx + dy*dy)
                        if dist < 0.1 or dist >= 20.0: continue
                        
                        sprite_angle = math.atan2(dy, dx) - pa
                        while sprite_angle < -math.pi: sprite_angle += 2.0 * math.pi
                        while sprite_angle > math.pi: sprite_angle -= 2.0 * math.pi
                        
                        if abs(sprite_angle) < (fov / 2.0) + 0.5:
                            screen_x = int((0.5 * (sprite_angle / (fov / 2.0)) + 0.5) * screen_w)
                            sprite_h = int(screen_h / dist)
                            sprite_w = sprite_h
                            
                            r_idx = int((screen_x / screen_w) * num_rays)
                            if 0 <= r_idx < num_rays and z_buffer[r_idx] > dist:
                                rc_s = RECT(screen_x - sprite_w//2, (screen_h - sprite_h)//2, screen_x + sprite_w//2, (screen_h + sprite_h)//2)
                                brush = hbrush_red if i >= 61 else hbrush_yellow
                                user32.FillRect(hdc, ctypes.byref(rc_s), brush)

                # Draw Radar Minimap
                map_size, cell_size = 16, 5
                offset_x, offset_y = screen_w - (map_size * cell_size) - 20, 20
                user32.FillRect(hdc, ctypes.byref(RECT(offset_x, offset_y, offset_x + map_size*cell_size, offset_y + map_size*cell_size)), hbrush_black)
                
                for y in range(map_size):
                    for x in range(map_size):
                        if WORLD_MAP[y][x] == 1:
                            user32.FillRect(hdc, ctypes.byref(RECT(offset_x + x*cell_size, offset_y + y*cell_size, offset_x + (x+1)*cell_size, offset_y + (y+1)*cell_size)), hbrush_wall)
                
                user32.FillRect(hdc, ctypes.byref(RECT(offset_x + int(px)*cell_size, offset_y + int(py)*cell_size, offset_x + (int(px)+1)*cell_size, offset_y + (int(py)+1)*cell_size)), gdi32.CreateSolidBrush(0x00FFFFFF))
                
                # Draw the 300-Nerve ANSM Firing Grid (Right Side, 15 rows x 20 columns)
                grid_rows, grid_cols = 15, 20
                box_w, box_h = 5, 5
                grid_x_start = screen_w - (grid_cols * (box_w + 2)) - 20
                grid_y_start = offset_y + (map_size * cell_size) + 15
                
                # Draw background label for the nerve matrix
                gdi32.SetTextColor(hdc, 0x0000FF00)
                gdi32.SetBkMode(hdc, 1)
                rc_lbl = RECT(grid_x_start, grid_y_start - 12, screen_w - 20, grid_y_start)
                user32.DrawTextW(hdc, "ANSM 300-NERVE SYSTEM MATRIX", -1, ctypes.byref(rc_lbl), 0)

                for r in range(grid_rows):
                    for c in range(grid_cols):
                        idx = r * grid_cols + c
                        if idx < 300:
                            state = nerve_states[idx]
                            color_val = NERVES_DATA[idx][2]
                            # Blend color based on firing state
                            if state > 0.1:
                                r_c = int(((color_val >> 16) & 0xFF) * state)
                                g_c = int(((color_val >> 8) & 0xFF) * state)
                                b_c = int((color_val & 0xFF) * state)
                                brush_color = (r_c << 16) | (g_c << 8) | b_c
                            else:
                                brush_color = 0x00222222 # Inactive / Dim grey
                            
                            brush = gdi32.CreateSolidBrush(brush_color)
                            bx = grid_x_start + c * (box_w + 2)
                            by = grid_y_start + r * (box_h + 2)
                            user32.FillRect(hdc, ctypes.byref(RECT(bx, by, bx + box_w, by + box_h)), brush)
                            gdi32.DeleteObject(brush)

                # Diagnostic info overlay
                rc_cpu = RECT(10, 10, 500, 50)
                gdi32.SetTextColor(hdc, 0x000000FF if amsv_block.cpu_temp > 50 else 0x00FFFFFF)
                user32.DrawTextW(hdc, f"ANSM CORE ACTIVE | CPU: {amsv_block.cpu_temp:.1f}% | ENGINE LIMIT: {amsv_block.gpu_load*100:.0f}%", -1, ctypes.byref(rc_cpu), 0)

                # Show real-time telemetry from one random active nerve
                active_nerves = [i for i, val in enumerate(nerve_states) if val > 0.8]
                if active_nerves:
                    fired_idx = random.choice(active_nerves)
                    nerve_id, nerve_name, _ = NERVES_DATA[fired_idx]
                    rc_log = RECT(10, screen_h - 30, 600, screen_h)
                    gdi32.SetTextColor(hdc, 0x0000FF00)
                    user32.DrawTextW(hdc, f"SIGNAL: [{nerve_id}] {nerve_name} -> EMITTING OK", -1, ctypes.byref(rc_log), 0)

                user32.ReleaseDC(0, hdc)
                time.sleep(0.016 / throttle) 
                
        except Exception:
            pass

# -------------------------------------------------------------------------
# 7. SOFTWARE ENGINE: PHYSICS & SWARM AI (CAIN)
# -------------------------------------------------------------------------
def physics_nerve():
    amsv_block.entities[0].x, amsv_block.entities[0].y = -650.0, -650.0 # Spawn at 1,1
    
    # Initialize Swarm (IDs 61-90)
    for i in range(61, 91):
        amsv_block.entities[i].x = (WORLD_MAP[8][8] * 100) - 800 + (i*10)
        amsv_block.entities[i].y = (WORLD_MAP[8][8] * 100) - 800 + (i*10)
        amsv_block.entities[i].health = 100.0

    while True:
        me, kb = amsv_block.entities[0], amsv_block.keyboard_state
        if amsv_block.state == 5:
            if (kb & (1 << 7)) != 0: amsv_block.state = 0 # Enter
            time.sleep(0.016)
            continue
            
        # Player Movement
        speed = 10.0
        new_x, new_y = me.x, me.y
        if (kb & (1 << 0)) != 0: 
            new_x += math.cos(me.ry) * speed; new_y += math.sin(me.ry) * speed
        if (kb & (1 << 2)) != 0: 
            new_x -= math.cos(me.ry) * speed; new_y -= math.sin(me.ry) * speed
        if (kb & (1 << 1)) != 0: me.ry -= 0.1
        if (kb & (1 << 3)) != 0: me.ry += 0.1
        
        grid_x, grid_y = int(new_x / 100.0 + 8.0), int(new_y / 100.0 + 8.0)
        if 0 <= grid_x < 16 and 0 <= grid_y < 16:
            if WORLD_MAP[grid_y][grid_x] == 0:
                me.x, me.y = new_x, new_y
                
        # Bullet Logic (IDs 1-10)
        if (kb & (1 << 4)) != 0: # Fire
            for i in range(1, 11):
                if amsv_block.entities[i].z == 0: # Inactive
                    amsv_block.entities[i].x, amsv_block.entities[i].y = me.x, me.y
                    amsv_block.entities[i].vx = math.cos(me.ry) * 30.0
                    amsv_block.entities[i].vy = math.sin(me.ry) * 30.0
                    amsv_block.entities[i].z = 1.0 # Active
                    break
                    
        for i in range(1, 11):
            if amsv_block.entities[i].z > 0:
                amsv_block.entities[i].x += amsv_block.entities[i].vx
                amsv_block.entities[i].y += amsv_block.entities[i].vy
                
                # Check collision with walls
                bx, by = int(amsv_block.entities[i].x / 100.0 + 8.0), int(amsv_block.entities[i].y / 100.0 + 8.0)
                if WORLD_MAP[by][bx] == 1:
                    amsv_block.entities[i].z = 0 # Destroy bullet
                else:
                    # Check collision with swarm
                    for s in range(61, 91):
                        if amsv_block.entities[s].health > 0:
                            dist = math.sqrt((amsv_block.entities[i].x - amsv_block.entities[s].x)**2 + (amsv_block.entities[i].y - amsv_block.entities[s].y)**2)
                            if dist < 50.0:
                                amsv_block.entities[s].health -= 50.0
                                amsv_block.entities[i].z = 0
                                break
                                
        # Swarm AI Logic
        for i in range(61, 91):
            if amsv_block.entities[i].health > 0:
                dx = me.x - amsv_block.entities[i].x
                dy = me.y - amsv_block.entities[i].y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 10.0 and dist < 800.0: # Chase Player
                    amsv_block.entities[i].x += (dx/dist) * 2.0
                    amsv_block.entities[i].y += (dy/dist) * 2.0

        time.sleep(0.016)

# -------------------------------------------------------------------------
# 8. GRAND UNIFICATION ENTRY POINT
# -------------------------------------------------------------------------
if __name__ == '__main__':
    print("\n=========================================================")
    print(" SOLO ROCK V4: ULTIMATE ANSM 300 MONOLITHIC EDITION")
    print(" All 300 Nerve Channels Unified into one System Matrix!")
    print("=========================================================\n")
    
    amsv_block.state = 5
    amsv_block.gpu_load = 1.0 
    
    threads = [
        threading.Thread(target=ai_hardware_overlord, daemon=True),
        threading.Thread(target=input_nerve, daemon=True),
        threading.Thread(target=audio_nerve, daemon=True),
        threading.Thread(target=physics_nerve, daemon=True),
        threading.Thread(target=update_ansm_telemetry, daemon=True)
    ]
    for t in threads: t.start()
    
    try:
        render_nerve() 
    except KeyboardInterrupt:
        print("\n[SYSTEM] Terminating Neural Link...")
