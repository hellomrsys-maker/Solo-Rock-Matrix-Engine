import ctypes
import math
import threading
import time
import sys
import os
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
# 2. WORLD DATA
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
# 3. AI HARDWARE CONTROLLER (THE OVERLORD)
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
# 4. SENSORY INPUT & AUDIO
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
# 5. SOFTWARE ENGINE: RENDERER (PPVO)
# -------------------------------------------------------------------------
def render_nerve():
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

    hbrush_floor = gdi32.CreateSolidBrush(0x00333333)
    hbrush_ceil = gdi32.CreateSolidBrush(0x00111111)
    hbrush_wall = gdi32.CreateSolidBrush(0x0000FF00) # Green Walls
    hbrush_red = gdi32.CreateSolidBrush(0x000000FF) # Enemies
    hbrush_yellow = gdi32.CreateSolidBrush(0x0000FFFF) # Bullets
    
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
                    title += "ALL SYSTEMS UNIFIED IN A SINGLE FILE.\n"
                    title += "The AI Overlord controls hardware capacity in real-time.\n"
                    title += "Avoid the Swarm. Escape the Matrix.\n\n"
                    title += "PRESS ENTER TO INITIALIZE NEURAL LINK...\n"
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

                # Draw Radar and Diagnostics
                map_size, cell_size = 16, 6
                offset_x, offset_y = screen_w - (map_size * cell_size) - 20, 20
                user32.FillRect(hdc, ctypes.byref(RECT(offset_x, offset_y, offset_x + map_size*cell_size, offset_y + map_size*cell_size)), gdi32.CreateSolidBrush(0x000000))
                
                for y in range(map_size):
                    for x in range(map_size):
                        if WORLD_MAP[y][x] == 1:
                            user32.FillRect(hdc, ctypes.byref(RECT(offset_x + x*cell_size, offset_y + y*cell_size, offset_x + (x+1)*cell_size, offset_y + (y+1)*cell_size)), hbrush_wall)
                
                user32.FillRect(hdc, ctypes.byref(RECT(offset_x + int(px)*cell_size, offset_y + int(py)*cell_size, offset_x + (int(px)+1)*cell_size, offset_y + (int(py)+1)*cell_size)), gdi32.CreateSolidBrush(0x00FFFFFF))
                
                rc_cpu = RECT(10, 10, 400, 50)
                gdi32.SetTextColor(hdc, 0x000000FF if amsv_block.cpu_temp > 50 else 0x00FFFFFF)
                gdi32.SetBkMode(hdc, 1)
                user32.DrawTextW(hdc, f"AI MONOLITHIC CORE | CPU: {amsv_block.cpu_temp:.1f}% | ENGINE LIMIT: {amsv_block.gpu_load*100:.0f}%", -1, ctypes.byref(rc_cpu), 0)

                user32.ReleaseDC(0, hdc)
                time.sleep(0.016 / throttle) 
                
        except Exception:
            pass

# -------------------------------------------------------------------------
# 6. SOFTWARE ENGINE: PHYSICS & SWARM AI (CAIN)
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
# 7. GRAND UNIFICATION ENTRY POINT
# -------------------------------------------------------------------------
if __name__ == '__main__':
    print("\n=========================================================")
    print(" SOLO ROCK V4: ULTIMATE MONOLITHIC EDITION")
    print(" All Swarm AI, Audio, Engine & Hardware Logic Unified!")
    print("=========================================================\n")
    
    amsv_block.state = 5
    amsv_block.gpu_load = 1.0 
    
    threads = [
        threading.Thread(target=ai_hardware_overlord, daemon=True),
        threading.Thread(target=input_nerve, daemon=True),
        threading.Thread(target=audio_nerve, daemon=True),
        threading.Thread(target=physics_nerve, daemon=True)
    ]
    for t in threads: t.start()
    
    try:
        render_nerve() 
    except KeyboardInterrupt:
        print("\n[SYSTEM] Terminating Neural Link...")
