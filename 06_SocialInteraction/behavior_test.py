import asyncio
from spherov2 import scanner
from spherov2 import toy
from spherov2.sphero_edu import SpheroEduAPI
from spherov2.types import Color
import numpy

GREEN = Color(20, 250, 25)
BLACK = Color(0, 0, 0)


def register_animations(sphero):
    sphero.register_matrix_animation(
        frames=[
            numpy.rot90(
                [
                    [1, 1, 5, 1, 5, 1, 5, 1],
                    [1, 1, 5, 5, 5, 5, 5, 5],
                    [5, 1, 5, 5, 5, 5, 5, 5],
                    [5, 5, 5, 5, 5, 5, 5, 5],
                    [5, 5, 5, 5, 5, 5, 5, 5],
                    [1, 5, 5, 5, 5, 5, 5, 5],
                    [1, 1, 5, 5, 5, 5, 5, 1],
                    [1, 1, 1, 5, 5, 5, 1, 1],
                ]
            )
        ],
        palette=[
            Color(255, 255, 255),
            Color(0, 0, 0),
            Color(255, 0, 0),
            Color(255, 64, 0),
            Color(255, 128, 0),
            Color(255, 191, 0),
            Color(255, 255, 0),
            Color(185, 246, 30),
            Color(0, 255, 0),
            Color(185, 255, 255),
            Color(0, 255, 255),
            Color(0, 0, 255),
            Color(145, 0, 211),
            Color(157, 48, 118),
            Color(255, 0, 255),
            Color(204, 27, 126),
        ],
        fps=10,
        transition=0,
    )


async def fist_bump(toy):
    with SpheroEduAPI(toy) as sphero:
        duration = 0.3
        sphero.set_main_led(BLACK)
        sphero.set_front_led(GREEN)
        sphero.set_heading(0)

        register_animations(sphero)
        sphero.play_matrix_animation(0, False)
        sphero.roll(0, 50, duration)
        await asyncio.sleep(duration)
        sphero.roll(180, -50, duration)
        await asyncio.sleep(duration)
        sphero.set_heading(0)
        sphero.set_speed(0)
        sphero.set_main_led(BLACK)


async def trick_spin(sphero):
    sphero.spin(360, 0.5)
    await asyncio.sleep(0.5)


async def excited_yes(sphero):
    sphero.set_speed(50)
    sphero.spin(360, 1)
    sphero.set_speed(0)


async def play_catch(sphero):
    await asyncio.sleep(1)
    # First leg
    sphero.spin(180, 0.5)
    await asyncio.sleep(0.5)
    sphero.set_speed(25)
    await asyncio.sleep(0.75)
    sphero.set_speed(0)
    # Turn back and check in
    sphero.spin(-180, 0.5)
    await asyncio.sleep(3)
    sphero.spin(180, 0.5)
    await asyncio.sleep(0.5)
    sphero.set_speed(25)
    await asyncio.sleep(0.6)
    sphero.set_speed(0)
    # Second leg
    sphero.spin(180, 0.5)
    await asyncio.sleep(3)
    # Nudge left
    sphero.spin(90, 0.25)
    await asyncio.sleep(0.4)
    sphero.set_speed(25)
    await asyncio.sleep(0.4)
    sphero.set_speed(0)
    # Turn back to start
    sphero.spin(-90, 0.25)
    # Wait
    await asyncio.sleep(4)
    # Yeet
    sphero.set_speed(150)
    await asyncio.sleep(2)
    sphero.set_speed(0)


async def main(sphero):
    # await fist_bump(sphero)
    with SpheroEduAPI(toy) as sphero:
        await play_catch(sphero)


if __name__ == "__main__":
    toy = scanner.find_toy(toy_name="SB-F11F")

    try:
        asyncio.run(main(toy))
    except KeyboardInterrupt:
        print("KeyboardInterrupt received, exiting...")
