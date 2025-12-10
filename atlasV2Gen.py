import numpy as np
import math
import sys

# ==========================================
# --- CONFIGURATION START ---
# ==========================================

# 1. Ring Configuration
# Format: Ring_Number: (LED_Count, Reverse_Direction)
# If Reverse_Direction is True, the ring is wired backwards (Zigzag / Right-to-Left).
# If Reverse_Direction is False, the ring is wired normally (Left-to-Right).

rings_config = {
    1:  (53, False),  # Ring 1
    2:  (59, True),   # Ring 2 (Reversed example)
    3:  (65, False),  # Ring 3
    4:  (69, True),   # Ring 4
    5:  (71, False),
    6:  (73, True),
    7:  (75, False),
    8:  (77, True),
    9:  (79, False),
    10: (81, True),
    11: (79, False),  # From here onwards, you can set specific directions
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

# 2. Global Vertical Flip
# Set to True if you want to flip the entire model upside down.
# (e.g., if Ring 1 is physically at the bottom).
flip_output_vertically = True

# 3. Grid Resolution
# 500 is the recommended balance between precision and editor visibility.
totalSize = 500

# ==========================================
# --- CONFIGURATION END ---
# ==========================================

def generate_ring_string(start_channel, pixel_count, grid_width, is_reversed=False):
    """
    Generates the comma-separated string for xLights with improved precision.
    """
    # Safety check
    if pixel_count > grid_width:
        print(f"ERROR: Ring with {pixel_count} LEDs is larger than totalSize {grid_width}.")
        sys.exit()

    result = [""] * grid_width
    
    # NEW LOGIC:
    # 1. Generate exact decimal positions from 0 to (width - 1)
    #    endpoint=True ensures the first pixel is exactly at the start and the last at the end.
    exact_positions = np.linspace(0, grid_width - 1, num=pixel_count, endpoint=True)
    
    current_channel = 0
    
    for pos in exact_positions:
        # 2. Use standard rounding (round) instead of ceiling (ceil)
        #    This ensures "Nearest Neighbor" precision.
        idx = int(round(pos))
        
        # Index overflow protection (just in case)
        if idx >= grid_width:
            idx = grid_width - 1
            
        result[idx] = start_channel + current_channel
        current_channel += 1
        
    if is_reversed:
        result.reverse()
        
    return ",".join(map(str, result))


# --- MAIN PROCESSING ---

current_led = 1
sphere_rows = []

# Iterate through rings in order (1 to 22)
for ring_num in sorted(rings_config.keys()):
    count, is_reversed = rings_config[ring_num]
    
    # Generate the string for this ring
    row_string = generate_ring_string(current_led, count, totalSize, is_reversed)
    
    # Add to our list of rows
    sphere_rows.append(row_string)
    
    # Increment channel counter
    current_led += count


# --- HANDLE GLOBAL FLIP ---
if flip_output_vertically:
    sphere_rows.reverse()


# --- WRITE XMODEL FILE ---

orig_stdout = sys.stdout
try:
    with open('atlas_v2.xmodel', 'w') as f:
        sys.stdout = f
        
        print('<?xml version="1.0" encoding="UTF-8"?>')
        print('<custommodel ')
        
        # Dynamic header generation
        header = (f'name="Atlas v2" parm1="{totalSize}" parm2="{len(rings_config)}" '
                  f'Depth="1" StringType="GRB Nodes" Transparency="0" PixelSize="2" '
                  f'ModelBrightness="0" Antialias="1" StrandNames="" NodeNames="" CustomModel="')
        
        footer = '" SourceVersion="2023.20"  >'
        
        # Join all rows with semicolons
        print(header + ";".join(sphere_rows) + footer)
        print('</custommodel>')
        
finally:
    sys.stdout = orig_stdout
    print("xModel file created successfully.")


# --- WRITE CSV SUMMARY ---

try:
    with open('atlas_v2.csv', 'w') as f:
        sys.stdout = f
        
        print("Ring,Direction,LED Count,Start Channel,End Channel")
        
        # Reset counter for CSV reporting logic to match the generation order
        # Note: If flipped vertically, the physical order might look different,
        # but here we list them by Ring ID logic.
        
        report_led = 1
        for ring_num in sorted(rings_config.keys()):
            count, is_reversed = rings_config[ring_num]
            
            direction_str = "Reverse ( <--- )" if is_reversed else "Normal ( ---> )"
            end_led = report_led + count - 1
            
            print(f"{ring_num},{direction_str},{count},{report_led},{end_led}")
            
            report_led += count

finally:
    sys.stdout = orig_stdout
    print("CSV file created successfully.")
