import asyncio
import cv2
import functools
from enum import Enum

from deepface import DeepFace
import speech_recognition as sr
from spherov2 import scanner
from spherov2 import toy
from spherov2.sphero_edu import SpheroEduAPI
from spherov2.types import Color

from animations import ANIMATIONS, get_animation_index


TEAL = Color(0, 255, 50)
BLACK = Color(0, 0, 0)
RED = Color(250, 15, 20)
BLUE = Color(25, 20, 250)
NEGATIVE_EMOTIONS = ("sad", "surprised", "angry", "fear")
POSITIVE_EMOTIONS = ("happy",)


class DemoPhases(Enum):
    START = 1
    MID = 2
    END = 3


initialized = False
current_phase = DemoPhases.START


async def fist_bump(sphero, heading=0):
    duration = 0.3
    sphero.play_matrix_animation(get_animation_index("fist_bump"), False)
    sphero.roll(heading, 50, duration)
    await asyncio.sleep(duration)
    sphero.roll((heading + 180) % 360, -50, duration)
    await asyncio.sleep(duration)
    sphero.set_heading(heading)
    await asyncio.sleep(1)
    sphero.clear_matrix()


async def spin(sphero, heading=0):
    sphero.spin(360, 0.5)
    await asyncio.sleep(0.5)


async def confused(sphero):
    sphero.play_matrix_animation(get_animation_index("confused"), False)
    sphero.spin(45, 0.5)
    await asyncio.sleep(0.5)
    sphero.spin(-90, 0.5)
    await asyncio.sleep(0.5)
    sphero.spin(45, 0.25)
    await asyncio.sleep(0.25)


async def blink_leds(sphero, color, num_times=3, period=0.5):
    for _i in range(num_times):
        sphero.set_front_led(color)
        sphero.set_back_led(color)
        await asyncio.sleep(period / 2)
        sphero.set_front_led(BLACK)
        sphero.set_back_led(BLACK)
        await asyncio.sleep(period / 2)


async def happy(sphero):
    # await blink_leds(sphero, YELLOW, 3, 0.1)
    sphero.play_matrix_animation(get_animation_index("happy"), False)
    # sphero.set_main_led(BLACK)


async def say_no(sphero, args):
    sphero.set_front_led(RED)
    offset = 30
    sphero.spin(offset, 0.15)
    sphero.spin(-2 * offset, 0.15)
    sphero.spin(2 * offset, 0.15)
    sphero.spin(-offset, 0.15)
    sphero.set_front_led(BLUE)


async def say_yes(sphero, args):
    sphero.spin(360, 1)
    sphero.set_speed(0)
    sphero.play_matrix_animation(get_animation_index("happy"), False)
    await asyncio.sleep(3)
    sphero.clear_matrix()


async def approach(sphero):
    print("approaching")
    sphero.set_speed(25)
    print("speed 15")
    await asyncio.sleep(1)
    print("sleeping")
    sphero.set_speed(0)
    await asyncio.sleep(0.5)
    print("speed 0")
    sphero.play_matrix_animation(get_animation_index("confused"), False)
    print("matrix animation")
    await asyncio.sleep(2)
    sphero.clear_matrix()


async def catch(sphero, args):
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


def register_animations(sphero):
    for _id, anim in ANIMATIONS:
        sphero.register_matrix_animation(
            frames=anim["frames"],
            palette=anim["palette"],
            fps=anim["fps"],
            transition=anim["transition"],
        )


async def execute_command(sphero, command):
    sphero.set_speed(0)
    await asyncio.sleep(1)
    await COMMAND_MAP[command](sphero, 0)


async def sphero_behavior(toy, command_queue, affect_queue):
    global initialized, current_phase
    with SpheroEduAPI(toy) as sphero:
        sphero.set_main_led(BLACK)
        sphero.set_front_led(TEAL)

        if not initialized:
            register_animations(sphero)
            initialized = True
        while True:

            try:
                command = command_queue.get_nowait()
            except asyncio.QueueEmpty:
                command = None

            if current_phase in (DemoPhases.START, DemoPhases.END):
                try:
                    emotion = affect_queue.get_nowait()
                except asyncio.QueueEmpty:
                    emotion = None
                print(emotion)
                if emotion in NEGATIVE_EMOTIONS:
                    await approach(sphero)
                    current_phase = DemoPhases.MID

            if command:
                await execute_command(sphero, command)

            await asyncio.sleep(0.2)


def watch(video_stream):
    while True:
        ret, frame = video_stream.read()
        if not ret:
            break

        try:
            result = DeepFace.analyze(
                frame,
                actions=["emotion"],
                enforce_detection=False,  # don't crash if no face is detected
            )

            for face in result:
                emotion = face["dominant_emotion"]
                return emotion

        except Exception as e:
            # Ignore frames where no face is detected or an error occurs
            print("Warning:", e)


async def watch_wrapper(loop, affect_queue):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open camera")
        return
    while True:
        emotion = await loop.run_in_executor(None, functools.partial(watch, cap))
        if not emotion:
            continue
        await affect_queue.put(emotion)
        await asyncio.sleep(0.2)


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
        await asyncio.sleep(0.2)


COMMANDS = ["fist bump", "spin", "charger", "vector", "tricks", "fastball"]
RESPONSES = [fist_bump, spin, say_no, say_no, say_yes, catch]
COMMAND_MAP = {command: response for command, response in zip(COMMANDS, RESPONSES)}


async def main(sphero):
    loop = asyncio.get_running_loop()
    command_queue = asyncio.Queue()
    affect_queue = asyncio.Queue()

    tasks = [
        asyncio.create_task(watch_wrapper(loop, affect_queue)),
        asyncio.create_task(listen_wrapper(loop, command_queue)),
        asyncio.create_task(sphero_behavior(sphero, command_queue, affect_queue)),
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
