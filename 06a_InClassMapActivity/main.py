import asyncio

from spherov2 import scanner
from spherov2 import toy
from spherov2.sphero_edu import SpheroEduAPI
from aruco_detector import ArucoDetector
from aruco_obj import Aruco
import asyncio
import cv2
import numpy as np
import image_process_utils
import functools


async def watch(loop, command_queue):
    detector = ArucoDetector()
    await detector.begin_visualization()

    # run for 10 seconds
    await asyncio.sleep(1)

    await detector.end_visualization()
    print(detector.get_all_tag_centers())
    return detector.get_all_tag_centers()


async def aruco_wrapper(loop, command_queue):
    detector = ArucoDetector()
    await detector.begin_visualization()
    while True:
        await asyncio.sleep(0.1)
        res = detector.get_all_tag_centers()
        if res:
            breakpoint()
            print(res)


async def move_sphero(sphero, loop, command_queue):
    with SpheroEduAPI(toy) as sphero:
        sphero.spin(90, 0.5)
        pedestrian = None
        try:
            command = command_queue.get_nowait()
        except asyncio.QueueEmpty:
            command = None

        if pedestrian:
            await reroute(sphero, "right")  # TODO detect left or right


async def reroute(sphero, direction="left"):
    sphero.set_heading(-45 if direction is "left" else 45)
    sphero.set_speed(50)
    await asyncio.sleep(1)
    sphero.set_speed(0)


async def color_detection_wrapper(loop, command_queue, sphero):
    while True:
        await asyncio.sleep(1)
        detect_color_blocks()


def detect_color_blocks(img_path="captured_image.jpg"):
    """
    Detects red and yellow color blocks in the image and draws a bounding box around them.
    It now also returns a list of corner coordinates for the detected color blocks.

    Returns:
        list: A list of dictionaries, where each dictionary contains the
              'area' and 'corners' (Top-Left, Top-Right, Bottom-Right, Bottom-Left)
              of a detected color block's bounding box.
    """
    img = cv2.imread(img_path)
    if img is None:
        print(f"Error: Could not read image at {img_path}")
        return []  # Return empty list if image read fails

    # 1. Convert BGR image to HSV color space
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # --- Define HSV Ranges ---

    # YELLOW typically has Hue around 20-30 (in OpenCV's 0-179 range)
    # Hue, Saturation, Value
    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([40, 255, 255])
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # RED wraps around the 0/179 boundary, so we need two ranges
    # Range 1 (low end of hue)
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    # Range 2 (high end of hue)
    lower_red2 = np.array([170, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    # Combine the two red masks
    red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)

    # Combine the yellow and red masks
    combined_mask = cv2.bitwise_or(red_mask, yellow_mask)

    # Optional: Clean up the mask using morphological operations (Erode/Dilate)
    kernel = np.ones((5, 5), np.uint8)
    combined_mask = cv2.erode(combined_mask, kernel, iterations=1)
    combined_mask = cv2.dilate(combined_mask, kernel, iterations=1)

    # 2. Find contours (shapes) in the mask
    contours, _ = cv2.findContours(
        combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    output_img = img.copy()
    block_corners = []  # Initialize list to store corner data

    # 3. Iterate through contours and draw a bounding box for detected blocks
    for contour in contours:
        # Filter out small areas that are likely noise
        area = cv2.contourArea(contour)
        if area > 500:  # Adjust 500 based on the minimum size of your color blocks
            # Get the coordinates of the bounding rectangle (x, y, width, height)
            x, y, w, h = cv2.boundingRect(contour)

            # Draw a green rectangle (BGR: 0, 255, 0)
            cv2.rectangle(output_img, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Calculate the four corners of the bounding box
            # Order: Top-Left, Top-Right, Bottom-Right, Bottom-Left
            corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]

            # Store the corners and area
            block_corners.append({"area": area, "corners": corners})

    # Display the result
    cv2.imshow("Detected Color Blocks", output_img)
    cv2.waitKey(0)  # Waits indefinitely for a key press
    cv2.destroyAllWindows()

    # Return the list of detected corner coordinates
    return block_corners


async def main(sphero):
    loop = asyncio.get_running_loop()
    command_queue = asyncio.Queue()

    tasks = [
        asyncio.create_task(aruco_wrapper(loop, command_queue)),
        asyncio.create_task(move_sphero(sphero, loop, command_queue)),
        asyncio.create_task(color_detection_wrapper(loop, command_queue)),
    ]
    try:
        # Run until one of the tasks fails or is cancelled.
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        print("Main cancelled, shutting down...")
    finally:
        # Cancel all running tasks
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    toy = scanner.find_toy(toy_name="SB-F11F")
    try:
        asyncio.run(main(toy))
    except KeyboardInterrupt:
        print("KeyboardInterrupt received, exiting...")
