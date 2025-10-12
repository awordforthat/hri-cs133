import asyncio
import cv2
import functools
import random

from deepface import DeepFace
import speech_recognition as sr
from spherov2 import scanner
from spherov2 import toy
from spherov2.sphero_edu import SpheroEduAPI
from spherov2.types import Color
from spherov2 import utils

from animations import ANIMATIONS, get_animation_index


GREEN = Color(20, 250, 25)
BLACK = Color(0, 0, 0)
MAX_EMOTION_BUFFER_LENGTH = 10

initialized = False
last_command = None
emotion_buffer = []


def update_emotion_buffer(new_emotion):
    # lazy ring buffer
    global emotion_buffer
    emotion_buffer.append(new_emotion)
    if len(emotion_buffer) > MAX_EMOTION_BUFFER_LENGTH:
        emotion_buffer = emotion_buffer[1:]


def get_primary_emotion():
    return max(emotion_buffer, key=emotion_buffer.count)


async def fist_bump(sphero, heading=0, do_well=True):
    if do_well:
        duration = 0.3
        sphero.play_matrix_animation(get_animation_index("fist_bump"), False)
        sphero.roll(heading, 50, duration)
        await asyncio.sleep(duration)
        sphero.roll((heading + 180) % 360, -50, duration)
        await asyncio.sleep(duration)
        sphero.set_heading(heading)
    else:
        await confused(sphero)
    sphero.set_speed(0)
    sphero.set_main_led(BLACK)


async def confused(sphero):
    sphero.play_matrix_animation(get_animation_index("confused"), False)
    sphero.spin(45, 0.5)
    await asyncio.sleep(0.5)
    sphero.spin(-90, 0.5)
    await asyncio.sleep(0.5)
    sphero.spin(45, 0.25)
    await asyncio.sleep(0.25)


async def happy(sphero, heading, do_well=True):
    sphero.play_matrix_animation(get_animation_index("happy"), False)
    await asyncio.sleep(2)


def register_animations(sphero):
    for _id, anim in ANIMATIONS:
        sphero.register_matrix_animation(
            frames=anim["frames"],
            palette=anim["palette"],
            fps=anim["fps"],
            transition=anim["transition"],
        )


async def sphero_behavior(toy, command_queue, affect_queue):
    global initialized, last_command
    with SpheroEduAPI(toy) as sphero:
        sphero.set_main_led(BLACK)
        sphero.set_front_led(GREEN)

        if not initialized:
            # await calibrate(sphero)
            register_animations(sphero)
            initialized = True

        while True:
            try:
                command = command_queue.get_nowait()
            except asyncio.QueueEmpty:
                command = None

            try:
                emotion = affect_queue.get_nowait()
            except asyncio.QueueEmpty:
                emotion = None

            if emotion:
                update_emotion_buffer(emotion)

            if command:
                if command == "try again":
                    command = last_command
                last_command = command
                sphero.set_speed(0)
                await asyncio.sleep(1)
                await COMMAND_MAP[command](sphero, 0, do_well=random.randint(0, 10) > 5)
                # TODO: look for emotion response
            else:
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
        print("got text", text)
        if not text:
            continue
        for command in COMMANDS:
            if command in text:
                await command_queue.put(command)
                break
        await asyncio.sleep(0.2)


async def unimplemented(sphero):
    print("in unimplemented")


COMMANDS = ["fist bump", "play catch", "jump", "try again"]
RESPONSES = [fist_bump, unimplemented, unimplemented]
COMMAND_MAP = {command: response for command, response in zip(COMMANDS, RESPONSES)}


async def main(sphero):
    loop = asyncio.get_running_loop()
    command_queue = asyncio.Queue()
    affect_queue = asyncio.Queue()

    tasks = [
        asyncio.create_task(watch_wrapper(loop, affect_queue)),
        asyncio.create_task(sphero_behavior(sphero, command_queue, affect_queue)),
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
