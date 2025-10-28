import asyncio
from collections import deque
from datetime import datetime
from enum import Enum
import functools
from statistics import mean

from spherov2.sphero_edu import EventType
from spherov2.sphero_edu import SpheroEduAPI

from astar import a_star
from constants import BLACK, GREEN, GRID, RED, TEAL, WHITE, YELLOW
from grid_utils import follow_path, get_random_destination
from state import State


class StateName(Enum):
    INITIAL = "initial"
    CHOOSING = "choosing"
    EVADING = "evading"
    CHASING = "chasing"
    CAUGHT = "caught"
    TIMED_OUT = "timed_out"
    TERMINAL = "terminal"


class EventKey(Enum):
    COLLISION = "collision"
    LANDED = "landed"


class Initial(State):
    def __init__(self, sphero, name):
        super().__init__(sphero, name)

    async def start(self):
        self.sphero.set_front_led(TEAL)

    async def execute(self):
        # scroll_matrix_text should be blocking with the last param set to True
        # but it just isn't. Pretend it is by adding sleeps in between calls.
        self.sphero.scroll_matrix_text("Let's play tag!", WHITE, 30, True)
        await asyncio.sleep(3.5)
        self.sphero.set_matrix_character("3", WHITE)
        await asyncio.sleep(1)
        self.sphero.set_matrix_character("2", WHITE)
        await asyncio.sleep(1)
        self.sphero.set_matrix_character("1", WHITE)
        await asyncio.sleep(1)
        self.sphero.scroll_matrix_text("Go!!!", WHITE, 30, True)
        await asyncio.sleep(3)

        return StateName.CHOOSING

    async def stop(self):
        pass


class Choosing(State):
    def __init__(self, sphero, name):
        super().__init__(sphero, name)
        self.next_state = None
        self.yaw_buffer = deque(
            maxlen=5
        )  # assuming a polling rate of 10Hz, half a second of data

    async def start(self):
        self.sphero.set_stabilization(False)

    async def execute(self):
        while not self.next_state:
            gyro = self.sphero.get_gyroscope()
            self.yaw_buffer.append(gyro["z"])
            average = mean(self.yaw_buffer)

            # Spin clockwise for evading, counter clockwise for chasing
            if average < 0 and abs(average) > 100:
                self.next_state = StateName.EVADING
            if average > 0 and abs(average) > 100:
                self.next_state = StateName.CHASING

            await asyncio.sleep(0.1)
        return self.next_state

    async def stop(self):
        self.sphero.set_stabilization(True)


class Evading(State):
    duration = 10  # seconds

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
                    if (
                        light_result
                        and light_result > self.light_baseline * 1.25
                        or light_result < self.light_baseline * 0.5
                    ):
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
    duration = 10  # seconds

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
                print(light_result)
                await self.comms_queue.put(light_result)
            except Exception as e:
                print("check_light_wrapper error:", e)
            await asyncio.sleep(0.2)

    async def start(self):
        print("entering CHASING")
        self.start_time = datetime.now()
        self.light_baseline = self.sphero.get_luminosity()["ambient_light"]
        self.running = True
        self.sphero.set_main_led(RED)

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
                    if (
                        light_result
                        and light_result > light_result * self.light_baseline * 1.25
                        or light_result < self.light_baseline * 0.5
                    ):
                        print(light_result)
                        return StateName.TERMINAL  # lose condition
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


class Caught(State):
    def __init__(self, sphero, name):
        super().__init__(sphero, name)
        self.comms_queue = asyncio.Queue()
        self.tasks = []

    def flush_queue(self):
        while not self.comms_queue.empty():
            self.comms_queue.get_nowait()

    async def write_event(self, type):
        await self.comms_queue.put(type)

    def on_event(self, loop, type, _):
        event_write_task = loop.create_task(self.write_event(type))
        self.tasks.append(event_write_task)

    async def start(self):
        print("entering CAUGHT")
        self.flush_queue()
        loop = asyncio.get_running_loop()
        self.sphero.set_main_led(YELLOW)
        await asyncio.sleep(1)

        SpheroEduAPI.register_event(
            self.sphero,
            EventType.on_collision,
            functools.partial(self.on_event, loop, EventKey.COLLISION),
        )
        SpheroEduAPI.register_event(
            self.sphero,
            EventType.on_landing,
            functools.partial(self.on_event, loop, EventKey.LANDED),
        )
        self.sphero.scroll_matrix_text("You caught me!", WHITE, 30, True)
        await asyncio.sleep(2)
        self.sphero.scroll_matrix_text(
            "Tap to play again, toss to end game", WHITE, 30, True
        )
        await asyncio.sleep(4)

    async def execute(self):
        signals = []
        try:
            signals = []
            while not self.comms_queue.empty():
                signal = self.comms_queue.get_nowait()
                if signal:
                    signals.append(signal)
        except:
            print("exception")

        # Collision events are noisy and landings are hard to trigger.
        # Dump the whole queue and sort through the results to prioritize landings.
        if EventKey.LANDED in signals:
            return StateName.TERMINAL
        elif EventKey.COLLISION in signals:
            return StateName.INITIAL

        await asyncio.sleep(0.1)

    async def stop(self):
        for task in self.tasks:
            task.cancel()
        self.flush_queue()


class TimedOut(State):
    def __init__(self, sphero, name):
        super().__init__(sphero, name)

    async def start(self):
        print("entering TIMED OUT")
        pass

    async def execute(self):
        self.sphero.spin(720, 2)
        await asyncio.sleep(2)
        self.sphero.scroll_matrix_text("I got away!", WHITE, 30, True)
        await asyncio.sleep(4)
        return StateName.CHASING

    async def stop(self):
        self.sphero.set_speed(0)


class Terminal(State):
    duration = 15

    def __init__(self, sphero, name):
        super().__init__(sphero, name)
        self.start_time = 0

    async def start(self):
        self.start_time = datetime.now()

    async def execute(self):
        if (datetime.now() - self.start_time).total_seconds() < Terminal.duration:
            self.sphero.play_matrix_animation(0)

    async def stop(self):
        pass
