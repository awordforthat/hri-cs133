import asyncio

from spherov2 import scanner
from spherov2 import toy
from spherov2.sphero_edu import SpheroEduAPI

from astar import a_star
from constants import GREEN, GRID
from grid_utils import follow_path


async def main(sphero):
    sphero.set_front_led(GREEN)
    start = (1, 5)
    dest = (1, 3)
    path = a_star(start, dest, GRID)
    print(path)
    await follow_path(sphero, path)


if __name__ == "__main__":
    toy = scanner.find_toy(toy_name="SB-F11F")
    with SpheroEduAPI(toy) as sphero:
        try:
            asyncio.run(main(sphero))
        except KeyboardInterrupt:
            print("KeyboardInterrupt received, exiting...")
