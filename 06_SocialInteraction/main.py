import cv2
import functools
from deepface import DeepFace
import asyncio
import speech_recognition as sr
from spherov2 import scanner
from spherov2 import toy
from spherov2.sphero_edu import SpheroEduAPI
from spherov2.types import Color


GREEN = Color(20, 250, 25)
BLACK = Color(0, 0, 0)

COMMANDS = ["hello"]


async def sphero_behavior(toy, command_queue):
    with SpheroEduAPI(toy) as sphero:
        sphero.set_main_led(BLACK)
        sphero.set_front_led(GREEN)


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


async def watch_wrapper(loop, command_queue):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open camera")
        return
    while True:
        emotion = await loop.run_in_executor(None, functools.partial(watch, cap))
        if not emotion:
            continue
        print(emotion)
        await command_queue.put(emotion)


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

    tasks = [
        asyncio.create_task(watch_wrapper(loop, command_queue)),
        asyncio.create_task(sphero_behavior(sphero, command_queue)),
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
