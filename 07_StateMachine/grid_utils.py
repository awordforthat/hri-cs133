import asyncio
import math
import random


def get_random_destination(grid, current_location):
    """
    Assumes a grid of NxM as a list of lists. Blockages are represented by 1's.
    """
    result = None
    num_rows = len(grid)
    num_cols = len(grid[0])
    while result is None:
        random_y = random.randint(0, num_rows - 1)
        random_x = random.randint(0, num_cols - 1)
        if not grid[random_y][random_x] and (random_y, random_x) != current_location:
            result = (random_x, random_y)
    return result


def get_heading(start, end):
    if start == end:
        return None
    x = end[0] - start[0]
    y = end[1] - start[1]
    # gross
    if x == 0:
        if y < 0:
            return 0
        return 180

    if y == 0:
        if x < 0:
            return -90
        return 90

    degrees = math.degrees(math.atan(y / x))

    if x >= 0 and y >= 0:
        return degrees + 90
    if x <= 0 and y >= 0:
        return degrees - 90
    if x <= 0 and y <= 0:
        return degrees - 90
    if x >= 0 and y <= 0:
        return degrees + 90


async def follow_path(sphero, path):
    current_location = path[0]
    step_num = 0
    while step_num < len(path):
        direction = get_heading(current_location, path[step_num])
        if direction is None:
            step_num += 1
            continue
        sphero.set_heading(
            int(direction)  # sphero drive code chokes on floats, cast to int instead.
        )
        await asyncio.sleep(0.1)
        dist = math.dist(current_location, path[step_num])
        sleep_duration = 0.62 if dist == 1 else 0.8
        sphero.set_speed(75)
        await asyncio.sleep(sleep_duration if step_num <= 1 else sleep_duration * 0.55)
        sphero.set_speed(0)
        current_location = path[step_num]
        step_num += 1
        await asyncio.sleep(0.1)
    await asyncio.sleep(2)
