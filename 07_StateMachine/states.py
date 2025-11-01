import asyncio
from collections import deque
from datetime import datetime
from enum import Enum
import functools
from statistics import mean

from spherov2.sphero_edu import EventType
from spherov2.sphero_edu import SpheroEduAPI

from astar import a_star
from constants import BLACK, GREEN, GRID, LIGHT_THRESHHOLD, RED, TEAL, WHITE, YELLOW
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


global_position = (0, 0)
lost = None


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
        self.yaw_buffer = deque(
            maxlen=5
        )  # assuming a polling rate of 10Hz, half a second of data

    async def start(self):
        self.sphero.set_front_led(TEAL)  # necessary if we skip initial state
        self.sphero.set_stabilization(False)

    async def execute(self):

        next_state = None
        while not next_state:
            orientation = self.sphero.get_orientation()
            # wait for stability
            stable_pos = 10
            if (
                orientation["pitch"] < -stable_pos
                or orientation["pitch"] > stable_pos
                or orientation["roll"] < -stable_pos
                or orientation["roll"] > stable_pos
            ):
                await asyncio.sleep(0.2)
                continue
            gyro = self.sphero.get_gyroscope()
            self.yaw_buffer.append(gyro["z"])
            average = mean(self.yaw_buffer)
            if len(self.yaw_buffer) < 5:
                await asyncio.sleep(0.2)
                continue

            # Spin clockwise for evading, counter clockwise for chasing
            if average < 0 and abs(average) > 100:
                next_state = StateName.EVADING
            if average > 0 and abs(average) > 100:
                next_state = StateName.CHASING

            await asyncio.sleep(0.1)
        return next_state

    async def stop(self):
        self.sphero.set_stabilization(True)
        self.yaw_buffer.clear()


class Evading(State):
    duration = 10  # seconds

    def __init__(self, sphero, name):
        super().__init__(sphero, name)
        self.tasks = []
        self.comms_queue = asyncio.Queue()

    async def path_wrapper(self):
        global global_position
        while self.running:
            dest = get_random_destination(GRID, global_position)
            path = a_star(global_position, dest, GRID)
            await follow_path(self.sphero, path)
            global_position = path[-1]

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
        global global_position
        print("entering EVADE")
        self.sphero.set_heading(0)
        self.start_time = datetime.now()
        self.running = True
        self.sphero.set_main_led(GREEN)

        light_task = asyncio.create_task(self.check_light_wrapper())
        path_task = asyncio.create_task(self.path_wrapper())

        self.tasks.append(light_task)
        self.tasks.append(path_task)

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
                    if light_result is None:
                        continue
                    if light_result >= LIGHT_THRESHHOLD:
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
        self.tasks = []
        self.comms_queue = asyncio.Queue()

    async def path_wrapper(self):
        global global_position

        while self.running:
            dest = None
            path = None
            # Some destinations might be unreachable. A* returns False in that case.
            # Keep trying until we have a valid destination.
            while not path:
                dest = get_random_destination(GRID, global_position)
                path = a_star(global_position, dest, GRID)
            await follow_path(self.sphero, path)
            global_position = path[-1]

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
        global global_position
        print("entering CHASING", global_position)
        self.start_time = datetime.now()
        self.running = True
        self.sphero.set_main_led(RED)

        light_task = asyncio.create_task(self.check_light_wrapper())
        path_task = asyncio.create_task(self.path_wrapper())

        self.tasks.append(light_task)
        self.tasks.append(path_task)

    async def execute(self):
        global lost, global_position
        try:
            while self.running:
                if (
                    datetime.now() - self.start_time
                ).total_seconds() < Chasing.duration:
                    await asyncio.sleep(0.1)
                    # nested try catch, gross
                    try:
                        light_result = self.comms_queue.get_nowait()
                    except:
                        light_result = None
                    if light_result is None:
                        continue

                    if light_result >= LIGHT_THRESHHOLD:
                        lost = True
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
            "Toss to play again, tap to end game", WHITE, 30, True
        )
        await asyncio.sleep(4)

    async def execute(self):
        global lost
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
            return StateName.CHOOSING
        elif EventKey.COLLISION in signals:
            lost = False
            return StateName.TERMINAL

        await asyncio.sleep(0.1)

    async def stop(self):
        for task in self.tasks:
            task.cancel()
        self.flush_queue()


class TimedOut(State):
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
        print("entering TIMED_OUT")
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

        self.sphero.spin(720, 2)
        await asyncio.sleep(1)
        self.sphero.scroll_matrix_text(
            "Timed out! Toss to play again, tap to end game.", WHITE, 30, True
        )
        await asyncio.sleep(1)

    async def execute(self):
        global lost
        # Collision events are noisy and landings are hard to trigger.
        # Dump the whole queue and sort through the results to prioritize landings.
        try:
            signals = []
            while not self.comms_queue.empty():
                signal = self.comms_queue.get_nowait()
                if signal:
                    signals.append(signal)
        except:
            print("exception")

        print(signals)
        if EventKey.LANDED in signals:
            return StateName.CHOOSING
        elif EventKey.COLLISION in signals:
            lost = False
            return StateName.TERMINAL

        await asyncio.sleep(0.1)

    async def stop(self):
        self.sphero.set_speed(0)
        for task in self.tasks:
            task.cancel()
        self.flush_queue()


class Terminal(State):
    def __init__(self, sphero, name):
        super().__init__(sphero, name)
        self.start_time = 0

    async def start(self):
        self.start_time = datetime.now()

    async def execute(self):
        if lost is None:
            self.sphero.set_main_led(WHITE)
            print("Tie game! (how did you get here?)")
        elif lost:
            self.sphero.set_main_led(RED)
            print("Loserrrrr")
        else:
            self.sphero.set_main_led(GREEN)
            print("You win!")

    async def stop(self):
        pass
