from spherov2.types import Color

GRID = [
    [0, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 1],
    [0, 0, 0, 1, 0, 1],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0, 0],
]


A_STAR_VIDEO_GRID = [
    [0, 0, 0, 0, 0],
    [1, 0, 0, 1, 0],
    [0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 1, 0, 1, 0],
]

TINY_TEST_GRID = [[0, 0], [0, 0]]

TEAL = Color(0, 225, 75)
BLACK = Color(0, 0, 0)
RED = Color(250, 15, 20)
BLUE = Color(25, 20, 250)
GREEN = Color(25, 250, 10)
WHITE = Color(255, 255, 255)
YELLOW = Color(255, 255, 0)

LIGHT_THRESHHOLD = 280  # experimentally determined
