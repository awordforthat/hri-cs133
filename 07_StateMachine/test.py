import asyncio

from spherov2 import scanner
from spherov2 import toy
from spherov2.sphero_edu import SpheroEduAPI

from astar import a_star
from constants import GREEN, GRID, RED, TEAL
from grid_utils import follow_path, get_random_destination


async def main(sphero):
    # position = (0, 0)
    # dest = get_random_destination(GRID, position)
    # path = a_star(position, dest, GRID)
    # await follow_path(sphero, path)
    while True:
        sphero.set_main_led(RED)
        sphero.set_front_led(TEAL)
        print(sphero.get_luminosity()["ambient_light"])


if __name__ == "__main__":
    toy = scanner.find_toy(toy_name="SB-F11F")
    with SpheroEduAPI(toy) as sphero:
        try:
            asyncio.run(main(sphero))
        except KeyboardInterrupt:
            print("KeyboardInterrupt received, exiting...")
