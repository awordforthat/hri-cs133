import asyncio
import functools

from datetime import datetime
from enum import Enum
from astar import a_star
from constants import BLACK, GREEN, GRID, TEAL, WHITE
from grid_utils import follow_path, get_random_destination
from state import State


class StateName(Enum):
    INITIAL = "initial"
    EVADING = "evading"
    CHASING = "chasing"
    CAUGHT = "caught"
    TIMED_OUT = "timed_out"
    TERMINAL = "terminal"


class Initial(State):
    def __init__(self, sphero, name):
        super().__init__(sphero, name)

    async def start(self):
        self.sphero.set_front_led(TEAL)

    async def execute(self):
        # scroll_matrix_text should be blocking with the last param set to True
        # but it just isn't. Pretend it is by adding sleeps in between calls.
        # self.sphero.scroll_matrix_text("Let's play tag!", WHITE, 30, True)
        # await asyncio.sleep(3.5)
        # self.sphero.set_matrix_character("3", WHITE)
        # await asyncio.sleep(1)
        # self.sphero.set_matrix_character("2", WHITE)
        # await asyncio.sleep(1)
        # self.sphero.set_matrix_character("1", WHITE)
        # await asyncio.sleep(1)
        # self.sphero.scroll_matrix_text("Go!!!", WHITE, 30, True)
        # await asyncio.sleep(3)

        # return StateName.CHASING if random.randint(1, 10) <= 5 else StateName.EVADING
        return StateName.EVADING

    async def stop(self):
        pass


class Evading(State):
    duration = 15  # seconds

    def __init__(self, sphero, name):
        super().__init__(sphero, name)
        self.current_location = (0, 0)
        self.tasks = []
        self.comms_queue = asyncio.Queue()
        self.path_task = None
        self.light_baseline = 0

    async def path_wrapper(self, path):
        while self.running:
            await follow_path(self.sphero, self.current_location, path)

    def check_light_sensor(self):
        return self.sphero.get_luminosity()["ambient_light"]

    async def check_light_wrapper(self):
        loop = asyncio.get_running_loop()
        while self.running:
            try:
                light_result = await loop.run_in_executor(None, self.check_light_sensor)
                await self.comms_queue.put(light_result)
            except Exception as e:
                print("check_light_wrapper error:", e)
            await asyncio.sleep(0.2)

    async def start(self):
        self.start_time = datetime.now()
        self.light_baseline = self.sphero.get_luminosity()["ambient_light"]
        self.running = True
        self.sphero.set_main_led(GREEN)

        light_task = asyncio.create_task(self.check_light_wrapper())

        dest = get_random_destination(GRID, self.current_location)
        path = a_star(self.current_location, dest, GRID)
        self.path_task = asyncio.create_task(self.path_wrapper(path))

        self.tasks.append(light_task)
        self.tasks.append(self.path_task)

    async def execute(self):
        try:
            while self.running:
                if (
                    datetime.now() - self.start_time
                ).total_seconds() < Evading.duration:
                    await asyncio.sleep(0.1)
                    # nested try catch, gross
                    try:
                        light_result = self.comms_queue.get_nowait()
                    except:
                        light_result = None
                    if light_result and light_result > 200:
                        return StateName.CAUGHT
                else:
                    return StateName.TIMED_OUT
        except asyncio.CancelledError:
            pass  # allow clean exit

    async def stop(self):
        self.sphero.set_speed(0)
        self.sphero.set_main_led(BLACK)
        self.running = False
        for task in self.tasks:
            task.cancel()


class Chasing(State):
    def __init__(self, sphero, name):
        super().__init__(sphero, name)

    async def start(self):
        self.start_time = datetime.now()
        self.sphero.set_main_led(GREEN)

    async def execute(self):
        await asyncio.sleep(5)

    async def stop(self):
        pass


class Caught(State):
    def __init__(self, sphero, name):
        super().__init__(sphero, name)
        self.signal = None

    async def start(self):

        self.sphero.scroll_matrix_text("You caught me!", WHITE, 30, True)
        await asyncio.sleep(2)
        self.sphero.scroll_matrix_text(
            "Tap to play again, toss to end game", WHITE, 30, True
        )
        await asyncio.sleep(4)

    async def execute(self):
        while not self.signal:
            asyncio.sleep(0.1)

        return StateName.TERMINAL

    async def stop(self):
        pass


class TimedOut(State):
    def __init__(self, sphero, name):
        super().__init__(sphero, name)

    async def start(self):
        pass

    async def execute(self):
        self.sphero.spin(720, 2)
        await asyncio.sleep(2)
        self.sphero.scroll_matrix_text("I got away!", WHITE, 30, True)
        await asyncio.sleep(4)
        return StateName.TERMINAL

    async def stop(self):
        pass


class Terminal(State):
    def __init__(self, sphero, name):
        super().__init__(sphero, name)

    async def start(self):
        print("Starting terminal")

    async def execute(self):
        print("executing terminal")

    async def stop(self):
        print("stopping terminal")
