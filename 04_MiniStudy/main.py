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
DELAY_VALUE = 1  # Condition A is 1s. Condition B is 3s.

# Don't love this global but don't feel like refactoring the state machine.
is_wandering = True


def stop(sphero):
    global is_wandering
    sphero.set_speed(0)
    is_wandering = False


def lights_on(sphero, color=MAGENTA):
    sphero.set_front_led(color)
    sphero.set_back_led(color)
    sphero.set_main_led(color)


def lights_off(sphero):
    sphero.set_front_led(BLACK)
    sphero.set_back_led(BLACK)
    sphero.set_main_led(BLACK)


def cmd_wander(sphero):
    # sphero param unused here, but it needs to exist to match the paradigm of the callback functions.
    global is_wandering
    is_wandering = True


COMMANDS = ("stop", "lights on", "lights off", "wander")
RESPONSES = (stop, lights_on, lights_off, cmd_wander)
COMMAND_MAP = {command: response for command, response in zip(COMMANDS, RESPONSES)}


class MoveStates(Enum):
    SPIN = 0
    MOVE = 1
    PAUSE = 2


async def wander(toy, command_queue):
    states = [MoveStates.SPIN, MoveStates.MOVE, MoveStates.PAUSE]  # Gross, do better.
    # "Random" wander path so we keep consistency between experiment cases.
    heading_offsets = (90, 110, 20, 80, 60)
    heading_index = 0
    behavior_phase_index = 0

    with SpheroEduAPI(toy) as sphero:
        while True:
            try:
                command = command_queue.get_nowait()
                print(command)
            except asyncio.QueueEmpty:
                command = None

            if command:
                sphero.set_speed(0)
                sphero.spin(15, 0.01)
                # sphero.play_sound("Menu.Accept")  # Not working in API?
                sphero.set_main_led(GREEN)  # Acknowledge the command.
                await asyncio.sleep(DELAY_VALUE)
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
                    print("spin")
                    sphero.spin(heading_offsets[heading_index], 0.2)
                    heading_index = (heading_index + 1) % len(heading_offsets)
                    print("New heading index", heading_index)
                    behavior_phase_index = (behavior_phase_index + 1) % len(states)
                    continue
                case MoveStates.MOVE:
                    print("move")
                    sphero.set_speed(50)
                    await asyncio.sleep(0.75)
                    behavior_phase_index = (behavior_phase_index + 1) % len(states)
                    continue
                case MoveStates.PAUSE:
                    print("pause")
                    sphero.set_speed(0)
                    await asyncio.sleep(3)
                    behavior_phase_index = (behavior_phase_index + 1) % len(states)


def listen():
    r = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        # r.adjust_for_ambient_noise(source)
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
        # if text and any([command in text for command in COMMANDS]):
        #     print("Command", text)
        #     stop_event.set()
        #     print("Command received!")


async def main(sphero):
    loop = asyncio.get_running_loop()
    command_queue = asyncio.Queue()

    # Run wander and listen concurrently
    await asyncio.gather(
        wander(sphero, command_queue), listen_wrapper(loop, command_queue)
    )


print("Starting")
toy = scanner.find_toy()
asyncio.run(main(toy))
