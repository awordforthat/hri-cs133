# Note: Use with caution -- this has not been tested

import time
from spherov2 import scanner
from spherov2.sphero_edu import SpheroEduAPI
from spherov2.types import Color

# --- CONFIGURATION ---
TOY_NAME = "SB-AAAD"  # change this to your Sphero's name
MOVE_SPEED = 60       # movement speed
MOVE_TIME = 1.0       # seconds to move forward per step

# Example learned path (from simulation)
path = ["up", "up", "right", "down", "left", "up"]

# Map directions to angles (Sphero heading reference)
direction_to_heading = {
    "up": 0,
    "right": 90,
    "down": 180,
    "left": 270
}

toy = scanner.find_toy(toy_name=TOY_NAME)
with SpheroEduAPI(toy) as api:
    # Light up to show connection
    api.set_main_led(Color(r=0, g=255, b=0))
    time.sleep(1)

    # Start from a known heading
    api.set_heading(0)
    print("Starting navigation...")

    for move in path:
        heading = direction_to_heading[move]

        # Set Sphero's orientation
        api.set_heading(heading)

        # Move forward in that direction
        api.set_speed(MOVE_SPEED)
        time.sleep(MOVE_TIME)

        # Stop briefly between moves
        api.set_speed(0)
        time.sleep(0.5)

    # Done
    api.set_main_led(Color(r=0, g=0, b=255))
    print("Navigation complete!")