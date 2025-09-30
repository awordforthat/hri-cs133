import asyncio
import speech_recognition as sr
from spherov2 import scanner
from spherov2 import toy
from spherov2.sphero_edu import SpheroEduAPI
from spherov2.types import Color
from enum import Enum

GREEN = Color(20, 250, 25)
BLACK = Color(0, 0, 0)
MAGENTA = Color(239, 0, 255)
ORANGE = Color(255, 150, 0)
DELAY_VALUE = 3  # Condition A is 1s. Condition B is 3s.

# Don't love these globals but don't feel like refactoring the state machine.
is_wandering = True
is_compass_calibrated = False


def stop(sphero):
    global is_wandering
    sphero.set_speed(0)
    is_wandering = False


def lights_on(sphero, color=MAGENTA):
    set_lights(sphero, color)


def lights_off(sphero):
    set_lights(sphero, BLACK)


def set_lights(sphero, color):
    sphero.set_front_led(color)
    sphero.set_back_led(color)
    sphero.set_main_led(color)


def cmd_wander(_sphero):
    # sphero param unused here, but it exists to match the signatures of the other callback functions.
    global is_wandering
    is_wandering = True


COMMANDS = ("stop", "lights on", "lights off", "you're free")
RESPONSES = (stop, lights_on, lights_off, cmd_wander)
COMMAND_MAP = {command: response for command, response in zip(COMMANDS, RESPONSES)}


class MoveStates(Enum):
    SPIN = 0
    MOVE = 1
    PAUSE = 2


async def blink_main_led(sphero, color, intervals, on_duration=0.25, off_duration=0.25):
    for _count in range(intervals):
        sphero.set_main_led(color)
        await asyncio.sleep(on_duration)
        sphero.set_main_led(BLACK)
        await asyncio.sleep(off_duration)


async def wander(toy, command_queue):
    global is_compass_calibrated

    states = [MoveStates.SPIN, MoveStates.MOVE, MoveStates.PAUSE]  # Gross, do better.
    # "Random" wander path so we keep some consistency between experiment cases.
    heading_offsets = (90, 150, 270, 0, 150)
    heading_index = 0
    behavior_phase_index = 0

    with SpheroEduAPI(toy) as sphero:
        if not is_compass_calibrated:
            sphero.calibrate_compass()
            is_compass_calibrated = True
            sphero.set_main_led(BLACK)
        while True:
            sphero.set_front_led(ORANGE)
            try:
                command = command_queue.get_nowait()
                print(command)
            except asyncio.QueueEmpty:
                command = None

            if command:
                sphero.set_speed(0)
                face_origin(sphero)
                await asyncio.sleep(DELAY_VALUE)
                # sphero.play_sound(
                #     "Bolt.AudioMenu.Accept"
                # )  # Not working in community API?
                await blink_main_led(sphero, GREEN, 3)

                sphero.set_main_led(BLACK)  # Clear color
                COMMAND_MAP[command](sphero)

            if not is_wandering:
                heading_index = 0
                behavior_phase_index = 0
                await asyncio.sleep(0.2)
                continue

            # TODO: try to switch to a really tight loop based on delta times to increase responsiveness.
            match states[behavior_phase_index]:
                case MoveStates.SPIN:
                    sphero.set_compass_direction(heading_offsets[heading_index])
                    heading_index = (heading_index + 1) % len(heading_offsets)
                    behavior_phase_index = (behavior_phase_index + 1) % len(states)
                    continue
                case MoveStates.MOVE:
                    sphero.set_speed(40)

                    await asyncio.sleep(0.3)
                    behavior_phase_index = (behavior_phase_index + 1) % len(states)
                    continue
                case MoveStates.PAUSE:
                    sphero.set_speed(0)
                    await asyncio.sleep(1)
                    behavior_phase_index = (behavior_phase_index + 1) % len(states)


def face_origin(sphero):
    sphero.set_compass_direction(350)


def listen():
    r = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio).lower()
            print("Heard: ", text)
            return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"Recognition error: {e}")
            return None


async def listen_wrapper(loop, command_queue):
    while True:
        text = await loop.run_in_executor(None, listen)
        if not text:
            continue
        for command in COMMANDS:
            if command in text:
                await command_queue.put(command)
                break


async def main(sphero):
    loop = asyncio.get_running_loop()
    command_queue = asyncio.Queue()

    # Start tasks
    tasks = [
        asyncio.create_task(wander(sphero, command_queue)),
        asyncio.create_task(listen_wrapper(loop, command_queue)),
    ]

    try:
        # Run until one of the tasks fails or is cancelled
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
