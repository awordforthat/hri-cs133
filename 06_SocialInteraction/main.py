import cv2
import functools
import numpy

# from deepface import DeepFace
import asyncio
import speech_recognition as sr
from spherov2 import scanner
from spherov2 import toy
from spherov2.sphero_edu import SpheroEduAPI
from spherov2.types import Color
from spherov2 import utils

GREEN = Color(20, 250, 25)
BLACK = Color(0, 0, 0)

initialized = False


async def fist_bump(sphero):
    print("in fist bump routine")
    duration = 0.3
    sphero.play_matrix_animation(0, False)
    sphero.roll(0, 50, duration)
    await asyncio.sleep(duration)
    sphero.roll(180, -50, duration)
    await asyncio.sleep(duration)
    sphero.set_heading(0)
    sphero.set_speed(0)
    sphero.set_main_led(BLACK)


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


async def sphero_behavior(toy, command_queue, affect_queue):
    global initialized
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

            if command:
                sphero.set_speed(0)
                await asyncio.sleep(1)
                await COMMAND_MAP[command](sphero)
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


COMMANDS = ["hello", "fist bump", "play a game"]
RESPONSES = [unimplemented, fist_bump, unimplemented]
COMMAND_MAP = {command: response for command, response in zip(COMMANDS, RESPONSES)}


async def main(sphero):
    loop = asyncio.get_running_loop()
    command_queue = asyncio.Queue()
    affect_queue = asyncio.Queue()

    tasks = [
        # asyncio.create_task(watch_wrapper(loop, affect_queue)),
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
