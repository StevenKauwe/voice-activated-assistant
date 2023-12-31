import concurrent.futures
import signal
import time

import config
import keyboard
from kaaoao import Transcriber
from leo import AudioRecorder
from loguru import logger


def toggle_recording(recorder: AudioRecorder, transcriber: Transcriber):
    start_time = None
    while True:
        if start_time is not None:
            time_delta = time.time() - start_time
            if time_delta > config.TIMEOUT:
                logger.info("Timeout reached, exiting...")
                chunks = recorder.stop_recording()
                config.USE_SPEECH_TO_TEXT = False
                transcriber.transcribe_and_respond(chunks)
                start_time = None

        if keyboard.is_pressed(config.ACTIVATION_KEYS):
            if not recorder.is_recording:
                start_time = time.time()
                recorder.start_recording()
                time.sleep(0.15)  # Add a small delay
            else:
                chunks = recorder.stop_recording()
                transcriber.transcribe_and_respond(chunks)
                start_time = None

        if keyboard.is_pressed(config.EXIT_KEYS):
            logger.info("Exiting...")
            exit()


def continuous_recording_while_held(recorder, transcriber):
    while True:
        if keyboard.is_pressed(config.ACTIVATION_KEYS):
            if not recorder.is_recording:
                logger.info("Starting recording...")
                recorder.start_recording()

            while keyboard.is_pressed(config.ACTIVATION_KEYS):
                # Keep recording as long as the key is pressed
                time.sleep(0.1)  # Small delay to prevent high CPU usage

            if recorder.is_recording:
                logger.info("Stopping recording...")
                chunks = recorder.stop_recording()
                transcriber.transcribe_and_respond(chunks)
                logger.warning(f"press `{config.EXIT_KEYS}` to kill program")

        if keyboard.is_pressed(config.EXIT_KEYS):
            logger.info("Exiting...")
            exit()


def main():
    recorder = AudioRecorder()
    transcriber = Transcriber()

    if config.HOLD_TO_TALK:
        logger.info(f"Hold `{config.ACTIVATION_KEYS}` and speak for STT")
        continuous_recording_while_held(recorder=recorder, transcriber=transcriber)
    else:
        logger.info(
            f"Press `{config.ACTIVATION_KEYS}` to start recording and `{config.ACTIVATION_KEYS}` to stop"
        )
        toggle_recording(recorder=recorder, transcriber=transcriber)


def run():
    logger.info("Starting...")
    signal.signal(signal.SIGTERM, lambda signum, frame: exit())
    signal.signal(signal.SIGINT, lambda signum, frame: exit())
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(main)
        future.result()


if __name__ == "__main__":
    run()
