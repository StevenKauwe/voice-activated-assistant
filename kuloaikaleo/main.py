import concurrent.futures
import signal
import time

import config
import keyboard
from kaaoao import Transcriber
from leo import AudioRecorder
from loguru import logger


def main():
    recorder = AudioRecorder()
    transcriber = Transcriber()
    while True:
        if keyboard.is_pressed(config.ACTIVATION_KEYS):
            if not recorder.is_recording:
                recorder.start_recording()
                time.sleep(0.15)  # Add a small delay
            else:
                chunks = recorder.stop_recording()
                transcriber.transcribe_and_respond(chunks)
        if keyboard.is_pressed("esc"):
            logger.info("Exiting...")
            exit()


def run():
    signal.signal(signal.SIGTERM, lambda signum, frame: exit())
    signal.signal(signal.SIGINT, lambda signum, frame: exit())
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(main)
        future.result()


if __name__ == "__main__":
    run()
