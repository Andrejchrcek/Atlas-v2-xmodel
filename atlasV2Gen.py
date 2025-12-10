import numpy as np
import math
import sys

# ==========================================
# --- CONFIGURATION ---
# ==========================================

rings_config = {
    1:  (53, False),
    2:  (59, True),
    3:  (65, False),
    4:  (69, True),
    5:  (71, False),
    6:  (73, True),
    7:  (75, False),
    8:  (77, True),
    9:  (79, False),
    10: (81, True),  # Widest ring (Equator)
    11: (79, False),
    12: (77, True),
    13: (75, False),
    14: (73, True),
    15: (71, False),
    16: (69, True),
    17: (65, False),
    18: (59, True),
    19: (53, False),
    20: (45, True),
    21: (35, False),
    22: (19, True)
}

# Setting: Ring 1 is physically at the BOTTOM
# True = Ring 1 at bottom (bottom of sphere)
# False = Ring 1 at top (top of sphere)
FLIP_VERTICALLY = True

# 3D Grid Resolution
# 120 provides enough buffer if the model is taller than it is wide.
GRID_SIZE = 120

# 2D Matrix Width (for the 2D xmodel file)
MATRIX_WIDTH = 500

# ==========================================
# --- CALCULATION LOGIC ---
# ==========================================

def get_max_leds(rings):
    """Finds the maximum number of LEDs in a single ring."""
    return max(count for count, _ in rings.values())

def calculate_physically_accurate_positions(rings, grid_size, do_flip):
    """
    Calculates 3D positions so that the vertical spacing between rings
    is equal to the horizontal spacing between LEDs (1:1 aspect ratio).
    """
    positions = {}
    current_channel = 1
    
    max_leds = get_max_leds(rings)
    total_rings = len(rings)
    sorted_rings = sorted(rings.keys())
    
    # 1. Define Scale
    # How many voxels does the radius of the widest ring occupy?
    # Leave some padding on the sides (e.g., 10%)
    padding = grid_size * 0.1
    usable_radius = (grid_size / 2) - padding
    center = grid_size / 2
    
    # MATH:
    # Circumference of largest ring = max_leds * (led_pitch)
    # Radius = Circumference / 2pi
    # Therefore: Radius_in_LED_units = max_leds / (2 * pi)
    
    radius_in_led_units = max_leds / (2 * math.pi)
    
    # Key conversion: How many voxels equal one "LED pitch"?
    voxels_per_led_pitch = usable_radius / radius_in_led_units
    
    # Now we know the distance between rings must be exactly 'voxels_per_led_pitch'
    vertical_step = voxels_per_led_pitch
    
    # 2. Calculate total model height
    total_height_voxels = (total_rings - 1) * vertical_step
    
    # Check if it fits in the grid height
    if total_height_voxels > (grid_size - 2):
        print(f"WARNING: Model is too tall ({total_height_voxels:.1f} voxels). Increase GRID_SIZE!")
    
    # Center the model vertically
    start_y = (grid_size - total_height_voxels) / 2
    
    # 3. Generate positions
    for i, ring_num in enumerate(sorted_rings):
        count, is_reversed = rings[ring_num]
        
        # --- HEIGHT (Y) ---
        # If FLIP=True (Ring 1 at bottom):
        # Ring 1 (i=0) will have the largest Y (in xLights voxel logic, high Y is bottom)
        # Note: In xLights voxel logic, index 0 is TOP and index Max is BOTTOM.
        
        if do_flip:
            # Ring 1 (i=0) is bottom -> Y = start_y + total_height
            # Ring 22 is top -> Y = start_y
            grid_y = (start_y + total_height_voxels) - (i * vertical_step)
        else:
            # Ring 1 is top -> Y = start_y
            grid_y = start_y + (i * vertical_step)
            
        # --- WIDTH (Radius) ---
        # Radius of this ring relative to the largest one
        current_radius_led_units = count / (2 * math.pi)
        current_radius_voxels = current_radius_led_units * voxels_per_led_pitch
        
        # Generate points around circumference
        thetas = np.linspace(0, 2 * math.pi, num=count, endpoint=False)
        
        # Zigzag logic
        pixel_indices = list(range(count))
        if is_reversed:
            pixel_indices.reverse()
            
        for p_idx, theta in enumerate(thetas):
            # X, Z coordinates
            raw_x = current_radius_voxels * math.cos(theta)
            raw_z = current_radius_voxels * math.sin(theta)
            
            grid_x = int(round(center + raw_x))
            grid_z = int(round(center + raw_z))
            final_y = int(round(grid_y))
            
            # Clamp to grid boundaries
            grid_x = max(0, min(grid_size - 1, grid_x))
            final_y = max(0, min(grid_size - 1, final_y))
            grid_z = max(0, min(grid_size - 1, grid_z))
            
            ch_offset = pixel_indices[p_idx]
            positions[(grid_x, final_y, grid_z)] = current_channel + ch_offset
            
        current_channel += count
        
    return positions

def generate_voxel_string(positions, size):
    planes = []
    for z in range(size):
        rows = []
        for y in range(size):
            cols = []
            for x in range(size):
                val = positions.get((x, y, z), "")
                cols.append(str(val))
            rows.append(",".join(cols))
        planes.append(";".join(rows))
    return "|".join(planes)

def generate_2d_matrix(rings, width, do_flip):
    rows = []
    current_ch = 1
    sorted_rings = sorted(rings.keys())
    for r in sorted_rings:
        count, is_rev = rings[r]
        row_arr = [""] * width
        locs = np.linspace(0, width-1, num=count, endpoint=True)
        for i, pos in enumerate(locs):
            idx = int(round(pos))
            if idx >= width: idx = width-1
            row_arr[idx] = str(current_ch + i)
        if is_rev:
            row_arr.reverse()
        rows.append(",".join(row_arr))
        current_ch += count
    
    # If Flip is enabled, reverse the 2D rows so Ring 1 is at the bottom visually
    if do_flip:
        rows.reverse()
    return ";".join(rows)

# ==========================================
# --- GENERATION ---
# ==========================================

print("1. Calculating 3D positions (1:1 Spacing)...")
led_map_3d = calculate_physically_accurate_positions(rings_config, GRID_SIZE, FLIP_VERTICALLY)
voxel_data = generate_voxel_string(led_map_3d, GRID_SIZE)

print("2. Generating 2D Matrix...")
matrix_data = generate_2d_matrix(rings_config, MATRIX_WIDTH, FLIP_VERTICALLY)

# FILE 1: 3D VOXEL
xml_3d = f"""<?xml version="1.0" encoding="UTF-8"?>
<custommodel 
name="Atlas v2 3D" 
parm1="{GRID_SIZE}" 
parm2="{GRID_SIZE}" 
Depth="{GRID_SIZE}" 
StringType="GRB Nodes" 
Transparency="0" 
PixelSize="2" 
ModelBrightness="0" 
Antialias="1" 
StrandNames="" 
NodeNames="" 
CustomModel="{voxel_data}" 
SourceVersion="2023.20" >
</custommodel>"""

with open('atlas_v2_3D.xmodel', 'w') as f:
    f.write(xml_3d)
print("-> atlas_v2_3D.xmodel created.")

# FILE 2: 2D MATRIX
total_rings = len(rings_config)
xml_2d = f"""<?xml version="1.0" encoding="UTF-8"?>
<custommodel 
name="Atlas v2 2D" 
parm1="{MATRIX_WIDTH}" 
parm2="{total_rings}" 
Depth="1" 
StringType="GRB Nodes" 
Transparency="0" 
PixelSize="2" 
ModelBrightness="0" 
Antialias="1" 
StrandNames="" 
NodeNames="" 
CustomModel="{matrix_data}" 
SourceVersion="2023.20" >
</custommodel>"""

with open('atlas_v2_2D.xmodel', 'w') as f:
    f.write(xml_2d)
print("-> atlas_v2_2D.xmodel created.")

# FILE 3: CSV
try:
    with open('atlas_v2.csv', 'w') as f:
        f.write("Ring,Direction,LED Count,Start Channel,End Channel\n")
        report_led = 1
        for ring_num in sorted(rings_config.keys()):
            count, is_reversed = rings_config[ring_num]
            direction_str = "Reverse ( <--- )" if is_reversed else "Normal ( ---> )"
            end_led = report_led + count - 1
            f.write(f"{ring_num},{direction_str},{count},{report_led},{end_led}\n")
            report_led += count
    print("-> atlas_v2.csv created.")
except Exception as e:
    print(f"Error: {e}")
