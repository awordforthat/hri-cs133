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
        random_row = random.randint(0, num_rows - 1)
        random_col = random.randint(0, num_cols - 1)
        if (
            not grid[random_row][random_col]
            and (random_row, random_col) != current_location
        ):
            result = (random_row, random_col)
    return result


def get_heading(start, end):
    if start == end:
        return None
    x = end[0] - start[0]
    y = end[1] - start[1]

    # gross
    if x == 0:
        if y < 0:
            return 270
        return 90

    if y == 0:
        if x < 0:
            return 180
        return 0

    return math.degrees(math.tan(y / x))


async def follow_path(sphero, start, path):
    current_location = start
    step_num = 0
    while step_num < len(path) - 1:
        direction = get_heading(current_location, path[step_num])
        if direction is None:
            step_num += 1
            continue
        sphero.set_heading(
            int(direction)  # sphero drive code chokes on floats, cast to int instead.
        )
        sphero.set_speed(100)
        await asyncio.sleep(1)
        step_num += 1
